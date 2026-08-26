"""RISK-X Risk Scoring, Decision, and Evidence Engine Package."""

from app.engine.scoring import calculate_risk_score
from app.engine.decision import (
    evaluate_decision,
    Decision,
    RiskLevel,
    ALLOW_THRESHOLD,
    REVIEW_THRESHOLD,
    BLOCK_THRESHOLD,
)
from app.engine.reasons import extract_risk_reasons
from app.engine.evidence import (
    extract_structured_evidence,
    generate_analyst_summary,
    EvidenceItem,
    EvidenceSeverity,
    EvidenceSignalCode,
)

__all__ = [
    "calculate_risk_score",
    "evaluate_decision",
    "Decision",
    "RiskLevel",
    "ALLOW_THRESHOLD",
    "REVIEW_THRESHOLD",
    "BLOCK_THRESHOLD",
    "extract_risk_reasons",
    "extract_structured_evidence",
    "generate_analyst_summary",
    "EvidenceItem",
    "EvidenceSeverity",
    "EvidenceSignalCode",
]
