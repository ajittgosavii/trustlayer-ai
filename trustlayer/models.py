"""
TrustLayer AI — Data Models
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Claim(BaseModel):
    text: str
    risk: str  # "high" | "medium" | "low"
    issue: Optional[str] = None


class TechniqueScores(BaseModel):
    semantic_entropy: float = Field(ge=0.0, le=1.0)
    self_consistency: float = Field(ge=0.0, le=1.0)
    source_verification: float = Field(ge=0.0, le=1.0)
    enterprise_grounding: float = Field(ge=0.0, le=1.0)
    claim_classification: float = Field(ge=0.0, le=1.0)
    pattern_recognition: float = Field(ge=0.0, le=1.0)
    temporal_consistency: float = Field(ge=0.0, le=1.0)
    numerical_validation: float = Field(ge=0.0, le=1.0)

    def weighted_confidence(self) -> float:
        weights = {
            "semantic_entropy":    0.10,
            "self_consistency":    0.12,
            "source_verification": 0.18,
            "enterprise_grounding":0.25,
            "claim_classification":0.10,
            "pattern_recognition": 0.08,
            "temporal_consistency":0.10,
            "numerical_validation":0.07,
        }
        total = sum(
            getattr(self, k) * w for k, w in weights.items()
        )
        return round(total * 100, 1)

    def as_dict(self) -> dict:
        labels = {
            "semantic_entropy":    "Semantic Entropy",
            "self_consistency":    "Self-Consistency",
            "source_verification": "Source Verification",
            "enterprise_grounding":"Enterprise Grounding",
            "claim_classification":"Claim Classification",
            "pattern_recognition": "Pattern Recognition",
            "temporal_consistency":"Temporal Consistency",
            "numerical_validation":"Numerical Validation",
        }
        return {labels[k]: round(getattr(self, k) * 100, 1)
                for k in labels}


class DetectionResult(BaseModel):
    # Core outputs
    query: str
    llm_response: str
    industry: str
    action: str                        # "PASS" | "FLAG" | "BLOCK"
    confidence_score: float            # 0–100
    risk_score: float                  # 0–100
    explanation: str

    # Technique breakdown
    scores: TechniqueScores

    # Issues
    issues: list[str] = []
    claims: list[Claim] = []
    fabrication_indicators: list[str] = []
    citations_found: list[str] = []
    citations_valid: bool = True
    numerical_issues: list[str] = []
    temporal_issues: list[str] = []

    # Meta
    timestamp: datetime = Field(default_factory=datetime.now)
    processing_ms: Optional[int] = None

    @property
    def action_color(self) -> str:
        return {"PASS": "#27AE60", "FLAG": "#F39C12", "BLOCK": "#E74C3C"}.get(self.action, "#64748B")

    @property
    def action_emoji(self) -> str:
        return {"PASS": "✅", "FLAG": "⚠️", "BLOCK": "🚫"}.get(self.action, "❓")


class AnalysisRequest(BaseModel):
    query: str
    industry: str = "General"
    context: Optional[str] = None          # enterprise grounding text
    self_consistency_check: bool = False   # adds 2 more LLM calls
