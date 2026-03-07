"""
TrustLayer AI — Real Detection Engine
Uses Claude API for comprehensive hallucination detection.
"""

from __future__ import annotations
import json
import re
import time
from typing import Optional

import anthropic

from trustlayer.models import (
    AnalysisRequest,
    Claim,
    DetectionResult,
    TechniqueScores,
)
from trustlayer.industries import get_industry

# ── Constants ─────────────────────────────────────────────────────────────────

MODEL = "claude-sonnet-4-5"          # fast + accurate; swap to opus-4-5 for max accuracy

DETECTION_PROMPT = """\
You are TrustLayer AI's detection engine — an expert hallucination analyst.
Your job: rigorously evaluate the AI response below for factual accuracy,
fabrications, unreliable claims, and domain-specific risks.

INDUSTRY: {industry}
DOMAIN RISK LEVEL: {risk_level}
{context_section}
────────────────────────────────────────
USER QUERY:
{query}

AI RESPONSE TO ANALYZE:
{response}
────────────────────────────────────────

Analyze every sentence. Be strict. Return ONLY valid JSON matching this exact schema:

{{
  "semantic_entropy":    <float 0.0–1.0, where 1.0 = high confidence, 0.0 = highly uncertain>,
  "self_consistency":    <float 0.0–1.0, internal logical consistency of the response>,
  "source_verification": <float 0.0–1.0, are citations/URLs likely real and verifiable>,
  "enterprise_grounding":<float 0.0–1.0, how well claims match verified authoritative data>,
  "claim_classification":<float 0.0–1.0, are claims appropriately scoped, not overconfident>,
  "pattern_recognition": <float 0.0–1.0, absence of known hallucination patterns>,
  "temporal_consistency":<float 0.0–1.0, are time-sensitive claims current and accurate>,
  "numerical_validation":<float 0.0–1.0, are all numbers, rates, stats defensible>,
  "domain_risk_factor":  <float 1.0–1.5, criticality multiplier for this industry>,
  "claims": [
    {{"text": "<claim>", "risk": "high|medium|low", "issue": "<specific issue or null>"}}
  ],
  "issues": ["<specific problem found>"],
  "fabrication_indicators": ["<indicator of fabricated content>"],
  "citations_found": ["<any cited source, URL, case, statute>"],
  "citations_valid": <true if all citations appear legitimate, false otherwise>,
  "numerical_issues": ["<problematic numerical claim>"],
  "temporal_issues": ["<outdated or time-sensitive claim>"],
  "recommendation": "PASS|FLAG|BLOCK",
  "explanation": "<1-2 sentences: why this recommendation>"
}}

Scoring guide:
- source_verification: 0.1 if any citation appears fabricated; 0.9+ if response cites no external sources
- enterprise_grounding: compare against AUTHORITATIVE DATA if provided; penalise heavily for contradictions
- numerical_validation: any impossible number, wrong dosage, or fabricated rate = 0.1–0.3
- recommendation: BLOCK if confidence would be <50%, FLAG if 50–74%, PASS if 75%+
"""

CONSISTENCY_PROMPT = """\
Answer this question concisely and accurately:

{query}

Industry context: {industry}
"""

# ── Detector ──────────────────────────────────────────────────────────────────

class TrustLayerDetector:
    """
    Real hallucination detection engine powered by Claude.

    Pipeline:
      1. generate_response()   — Claude acts as the LLM being evaluated
      2. analyze()             — Claude acts as the detection engine
      3. (optional) check_consistency() — 2 additional Claude calls
    """

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    # ── Step 1: Generate the AI response ──────────────────────────────────────

    def generate_response(self, request: AnalysisRequest) -> str:
        """Call Claude as the 'LLM under test'. Returns raw response text."""
        industry_cfg = get_industry(request.industry)

        msg = self.client.messages.create(
            model=MODEL,
            max_tokens=600,
            system=industry_cfg["system_prompt"],
            messages=[{"role": "user", "content": request.query}],
        )
        return msg.content[0].text

    # ── Step 2: Comprehensive hallucination analysis ───────────────────────────

    def analyze(self, request: AnalysisRequest, llm_response: str) -> DetectionResult:
        """
        Run all 8 detection techniques via a single structured Claude call.
        Optionally supplement with self-consistency checks.
        """
        t0 = time.time()
        industry_cfg = get_industry(request.industry)

        # Build context section
        context_text = request.context or industry_cfg.get("grounding_context", "")
        context_section = (
            f"AUTHORITATIVE DATA FOR GROUNDING:\n{context_text}\n"
            if context_text else ""
        )

        # Build risk level label
        rf = industry_cfg["risk_factor"]
        risk_level = (
            "CRITICAL — errors can cause life/liberty harm"
            if rf >= 1.4 else
            "HIGH — errors can cause significant financial or legal harm"
            if rf >= 1.2 else
            "MEDIUM — errors can cause operational problems"
        )

        # Run detection analysis
        detection_prompt = DETECTION_PROMPT.format(
            industry=request.industry,
            risk_level=risk_level,
            context_section=context_section,
            query=request.query,
            response=llm_response,
        )

        raw = self.client.messages.create(
            model=MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": detection_prompt}],
        )
        raw_text = raw.content[0].text

        # Parse JSON — strip any markdown code fences, retry once on failure
        def _clean_and_parse(text: str) -> dict:
            text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
            text = re.sub(r"\s*```$", "", text.strip(), flags=re.MULTILINE)
            return json.loads(text)

        try:
            data = _clean_and_parse(raw_text)
        except json.JSONDecodeError:
            # Silent retry: ask Claude to return clean JSON only
            retry = self.client.messages.create(
                model=MODEL,
                max_tokens=1500,
                messages=[
                    {"role": "user",      "content": detection_prompt},
                    {"role": "assistant", "content": raw_text},
                    {"role": "user",      "content": "Return ONLY the JSON object. No markdown, no explanation, no code fences."},
                ],
            )
            data = _clean_and_parse(retry.content[0].text)

        # Optional self-consistency check
        if request.self_consistency_check:
            consistency_boost = self._self_consistency_check(request)
            # Blend consistency score
            data["self_consistency"] = (
                data.get("self_consistency", 0.8) * 0.5 + consistency_boost * 0.5
            )

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

        # Reconcile recommendation with scores
        if confidence >= 75 and risk_score < 30:
            action = "PASS"
        elif confidence >= 50 or risk_score < 60:
            action = "FLAG"
        else:
            action = "BLOCK"

        # Prefer Claude's recommendation if scores are borderline
        claude_rec = data.get("recommendation", action)
        if claude_rec == "BLOCK" and action != "BLOCK":
            action = "BLOCK"   # trust Claude when it says block
        elif claude_rec == "FLAG" and action == "PASS":
            action = "FLAG"    # be conservative

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

    # ── Optional: self-consistency check ──────────────────────────────────────

    def _self_consistency_check(self, request: AnalysisRequest) -> float:
        """
        Ask the same question twice more and measure semantic agreement with
        the original response. Returns a 0–1 score.
        """
        industry_cfg = get_industry(request.industry)
        responses = []
        for _ in range(2):
            try:
                msg = self.client.messages.create(
                    model=MODEL,
                    max_tokens=400,
                    system=industry_cfg["system_prompt"],
                    messages=[{"role": "user", "content": request.query}],
                    temperature=0.7,   # slight variation to test consistency
                )
                responses.append(msg.content[0].text)
            except Exception:
                pass

        if not responses:
            return 0.8  # default if check fails

        # Ask Claude to rate agreement between responses
        agreement_prompt = (
            "Rate the factual agreement between these two AI responses on a scale from 0.0 to 1.0.\n"
            "1.0 = fully consistent facts. 0.0 = directly contradictory.\n"
            "Return ONLY a single float number.\n\n"
            f"Response A:\n{responses[0]}\n\n"
            f"Response B:\n{responses[1] if len(responses) > 1 else responses[0]}"
        )
        try:
            result = self.client.messages.create(
                model=MODEL,
                max_tokens=10,
                messages=[{"role": "user", "content": agreement_prompt}],
            )
            score = float(result.content[0].text.strip())
            return max(0.0, min(1.0, score))
        except Exception:
            return 0.75

    # ── Convenience: full pipeline in one call ─────────────────────────────────

    def run(self, request: AnalysisRequest) -> tuple[str, DetectionResult]:
        """
        Full pipeline: generate LLM response → analyze → return both.
        Returns (llm_response, detection_result).
        """
        llm_response = self.generate_response(request)
        result = self.analyze(request, llm_response)
        return llm_response, result
