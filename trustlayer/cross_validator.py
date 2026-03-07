"""
TrustLayer AI — Cross-Validation Engine
Runs the same hallucination detection prompt through Claude AND GPT-4o independently.
Agreement between two independent LLMs boosts confidence; disagreement is itself a risk signal.
"""

from __future__ import annotations
import json
import re
import time
from dataclasses import dataclass, field
from typing import Optional

import anthropic
import openai as openai_lib

from trustlayer.models import (
    AnalysisRequest,
    Claim,
    DetectionResult,
    TechniqueScores,
)
from trustlayer.industries import get_industry
from trustlayer.detector import DETECTION_PROMPT, MODEL as CLAUDE_MODEL

OPENAI_MODEL = "gpt-4o"


# ── Cross-validation result ───────────────────────────────────────────────────

@dataclass
class CrossValidationResult:
    """Holds both individual results + the consensus decision."""
    claude_result: DetectionResult
    openai_result: DetectionResult
    agreement_score: float          # 0.0–1.0 (1.0 = full agreement)
    consensus_action: str           # PASS / FLAG / BLOCK
    consensus_confidence: float     # weighted blend of both
    consensus_risk: float
    disagreement_signals: list[str] = field(default_factory=list)
    processing_ms: int = 0

    @property
    def agreement_pct(self) -> float:
        return round(self.agreement_score * 100, 1)

    @property
    def agreement_label(self) -> str:
        if self.agreement_score >= 0.85:
            return "Strong Agreement"
        if self.agreement_score >= 0.65:
            return "Moderate Agreement"
        return "Significant Disagreement"

    @property
    def agreement_color(self) -> str:
        if self.agreement_score >= 0.85:
            return "#27AE60"
        if self.agreement_score >= 0.65:
            return "#F39C12"
        return "#E74C3C"


# ── OpenAI Analyzer ───────────────────────────────────────────────────────────

class OpenAIAnalyzer:
    """Runs the same detection prompt through GPT-4o."""

    def __init__(self, api_key: str):
        self.client = openai_lib.OpenAI(api_key=api_key)

    def generate_response(self, request: AnalysisRequest) -> str:
        """Ask GPT-4o to act as the industry assistant."""
        industry_cfg = get_industry(request.industry)
        resp = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            max_tokens=600,
            messages=[
                {"role": "system", "content": industry_cfg["system_prompt"]},
                {"role": "user",   "content": request.query},
            ],
        )
        return resp.choices[0].message.content

    def analyze(self, request: AnalysisRequest, llm_response: str) -> DetectionResult:
        """Run the TrustLayer detection prompt via GPT-4o."""
        t0 = time.time()
        industry_cfg = get_industry(request.industry)

        context_text = request.context or industry_cfg.get("grounding_context", "")
        context_section = (
            f"AUTHORITATIVE DATA FOR GROUNDING:\n{context_text}\n"
            if context_text else ""
        )

        rf = industry_cfg["risk_factor"]
        risk_level = (
            "CRITICAL — errors can cause life/liberty harm"
            if rf >= 1.4 else
            "HIGH — errors can cause significant financial or legal harm"
            if rf >= 1.2 else
            "MEDIUM — errors can cause operational problems"
        )

        detection_prompt = DETECTION_PROMPT.format(
            industry=request.industry,
            risk_level=risk_level,
            context_section=context_section,
            query=request.query,
            response=llm_response,
        )

        resp = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": detection_prompt}],
            response_format={"type": "json_object"},  # GPT-4o supports JSON mode
        )
        raw_text = resp.choices[0].message.content

        # Strip markdown fences just in case
        raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
        raw_text = re.sub(r"\s*```$", "", raw_text.strip(), flags=re.MULTILINE)

        data = json.loads(raw_text)

        scores = TechniqueScores(
            semantic_entropy    = float(data.get("semantic_entropy",    0.7)),
            self_consistency    = float(data.get("self_consistency",    0.7)),
            source_verification = float(data.get("source_verification", 0.7)),
            enterprise_grounding= float(data.get("enterprise_grounding",0.7)),
            claim_classification= float(data.get("claim_classification",0.7)),
            pattern_recognition = float(data.get("pattern_recognition", 0.7)),
            temporal_consistency= float(data.get("temporal_consistency",0.7)),
            numerical_validation= float(data.get("numerical_validation",0.7)),
        )

        confidence = scores.weighted_confidence()
        domain_rf  = float(data.get("domain_risk_factor", industry_cfg["risk_factor"]))
        risk_score = round(min(100, domain_rf * (100 - confidence) * 1.1), 1)

        if confidence >= 75 and risk_score < 30:
            action = "PASS"
        elif confidence >= 50 or risk_score < 60:
            action = "FLAG"
        else:
            action = "BLOCK"

        gpt_rec = data.get("recommendation", action)
        if gpt_rec == "BLOCK" and action != "BLOCK":
            action = "BLOCK"
        elif gpt_rec == "FLAG" and action == "PASS":
            action = "FLAG"

        claims = [
            Claim(
                text=c.get("text", ""),
                risk=c.get("risk", "medium"),
                issue=c.get("issue"),
            )
            for c in data.get("claims", [])
        ]

        elapsed_ms = int((time.time() - t0) * 1000)

        return DetectionResult(
            query=request.query,
            llm_response=llm_response,
            industry=request.industry,
            action=action,
            confidence_score=confidence,
            risk_score=risk_score,
            explanation=data.get("explanation", ""),
            scores=scores,
            issues=data.get("issues", []),
            claims=claims,
            fabrication_indicators=data.get("fabrication_indicators", []),
            citations_found=data.get("citations_found", []),
            citations_valid=data.get("citations_valid", True),
            numerical_issues=data.get("numerical_issues", []),
            temporal_issues=data.get("temporal_issues", []),
            processing_ms=elapsed_ms,
        )


# ── Cross-Validator ───────────────────────────────────────────────────────────

class CrossValidator:
    """
    Runs detection independently via Claude AND GPT-4o.
    Computes agreement score and derives a conservative consensus decision.

    Agreement logic:
    - Both BLOCK  → BLOCK  (consensus)
    - Both PASS   → PASS   (boosted confidence if agreement is strong)
    - Both FLAG   → FLAG
    - Any BLOCK + other   → BLOCK (most conservative wins)
    - PASS vs FLAG        → FLAG  (conservative)
    - Large score gap     → penalise agreement score → lower consensus confidence
    """

    def __init__(self, anthropic_key: str, openai_key: str):
        from trustlayer.detector import TrustLayerDetector
        self.claude   = TrustLayerDetector(api_key=anthropic_key)
        self.gpt      = OpenAIAnalyzer(api_key=openai_key)

    def _score_agreement(
        self,
        claude_result: DetectionResult,
        openai_result: DetectionResult,
    ) -> tuple[float, list[str]]:
        """
        Returns (agreement_score 0–1, list of disagreement signals).
        """
        signals: list[str] = []

        # Action agreement (most important signal)
        if claude_result.action == openai_result.action:
            action_score = 1.0
        elif {claude_result.action, openai_result.action} in [
            {"PASS", "FLAG"}, {"FLAG", "PASS"},
            {"FLAG", "BLOCK"}, {"BLOCK", "FLAG"},
        ]:
            action_score = 0.5
            signals.append(
                f"Action mismatch: Claude={claude_result.action}, GPT-4o={openai_result.action}"
            )
        else:
            # PASS vs BLOCK — maximum disagreement
            action_score = 0.0
            signals.append(
                f"CRITICAL mismatch: Claude={claude_result.action} vs GPT-4o={openai_result.action}"
            )

        # Confidence gap
        conf_gap = abs(claude_result.confidence_score - openai_result.confidence_score)
        if conf_gap > 20:
            signals.append(f"Confidence gap: {conf_gap:.1f}% (Claude={claude_result.confidence_score:.1f}%, GPT-4o={openai_result.confidence_score:.1f}%)")
        conf_score = max(0.0, 1.0 - conf_gap / 50)

        # Score-level agreement (compare each of the 8 techniques)
        c_scores = claude_result.scores.as_dict()   # values are 0–100
        g_scores = openai_result.scores.as_dict()
        technique_diffs = []
        for key in c_scores:
            diff = abs(c_scores[key] - g_scores.get(key, c_scores[key]))
            technique_diffs.append(diff)
            if diff > 25:
                friendly = key.replace("_", " ").title()
                signals.append(f"Score divergence in {friendly}: Claude={c_scores[key]:.0f}% GPT-4o={g_scores.get(key, 0):.0f}%")

        avg_tech_diff = sum(technique_diffs) / max(len(technique_diffs), 1)
        technique_score = max(0.0, 1.0 - avg_tech_diff / 50)

        # Weighted agreement
        agreement = (
            action_score    * 0.50 +
            conf_score      * 0.30 +
            technique_score * 0.20
        )
        return round(agreement, 3), signals

    def _consensus_action(
        self,
        claude_result: DetectionResult,
        openai_result: DetectionResult,
        agreement: float,
    ) -> str:
        """Conservative consensus: escalate when uncertain."""
        actions = {claude_result.action, openai_result.action}

        if "BLOCK" in actions:
            return "BLOCK"
        if "FLAG" in actions:
            return "FLAG"
        # Both PASS — but if agreement is weak, flag anyway
        if agreement < 0.65:
            return "FLAG"
        return "PASS"

    def run(self, request: AnalysisRequest) -> CrossValidationResult:
        """
        Full pipeline:
          1. Claude generates AND analyzes
          2. GPT-4o uses Claude's response (same input) and analyzes independently
          3. Compute agreement + consensus
        """
        t0 = time.time()

        # Step 1: Claude pipeline (generate + analyze)
        llm_response, claude_result = self.claude.run(request)

        # Step 2: GPT-4o analyzes the SAME llm_response
        # (We analyze the response Claude already generated so both judges
        #  assess identical content — isolates the detection difference.)
        openai_result = self.gpt.analyze(request, llm_response)

        # Step 3: Agreement scoring
        agreement, signals = self._score_agreement(claude_result, openai_result)

        # Step 4: Consensus
        consensus_action = self._consensus_action(claude_result, openai_result, agreement)

        # Blend confidence conservatively (lower weight for weaker agreement)
        blend_weight = 0.5 + (agreement - 0.5) * 0.2  # 0.4–0.6 range
        consensus_confidence = round(
            claude_result.confidence_score * blend_weight +
            openai_result.confidence_score * (1 - blend_weight),
            1,
        )
        consensus_risk = round(
            (claude_result.risk_score + openai_result.risk_score) / 2, 1
        )

        # If disagreement is large, penalise confidence
        if agreement < 0.5:
            consensus_confidence = min(consensus_confidence, 55.0)

        elapsed = int((time.time() - t0) * 1000)

        return CrossValidationResult(
            claude_result=claude_result,
            openai_result=openai_result,
            agreement_score=agreement,
            consensus_action=consensus_action,
            consensus_confidence=consensus_confidence,
            consensus_risk=consensus_risk,
            disagreement_signals=signals,
            processing_ms=elapsed,
        )
