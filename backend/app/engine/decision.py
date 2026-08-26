"""
RISK-X Decision Engine Module
=============================
Applies deterministic policy thresholds to convert a 0-100 risk score into
an operational decision (ALLOW, REVIEW, BLOCK) and risk level tier (LOW, MEDIUM, HIGH).
"""

from enum import Enum
import math
from typing import Tuple, Union


class Decision(str, Enum):
    """Guarded operational response for payment transactions."""
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class RiskLevel(str, Enum):
    """Calibrated risk severity tier."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# Configurable Policy Threshold Constants
ALLOW_THRESHOLD: int = 39     # Scores 0..39 => ALLOW (LOW)
REVIEW_THRESHOLD: int = 69    # Scores 40..69 => REVIEW (MEDIUM)
BLOCK_THRESHOLD: int = 70     # Scores 70..100 => BLOCK (HIGH)


def evaluate_decision(risk_score: Union[int, float]) -> Tuple[Decision, RiskLevel]:
    """
    Evaluates policy thresholds on a risk score and returns a deterministic decision
    and corresponding risk level tier.

    Policy Matrix:
        - Score [0, 39]   => ALLOW,  RiskLevel.LOW
        - Score [40, 69]  => REVIEW, RiskLevel.MEDIUM
        - Score [70, 100] => BLOCK,  RiskLevel.HIGH

    Boundary Behavior:
        0   => (ALLOW, LOW)
        39  => (ALLOW, LOW)
        40  => (REVIEW, MEDIUM)
        69  => (REVIEW, MEDIUM)
        70  => (BLOCK, HIGH)
        100 => (BLOCK, HIGH)

    Args:
        risk_score: Integer or float risk score between 0 and 100.

    Returns:
        Tuple[Decision, RiskLevel]: The operational action and risk severity.

    Raises:
        TypeError: If risk_score is not a numeric value.
        ValueError: If risk_score is outside [0, 100], NaN, or infinite.
    """
    if risk_score is None or isinstance(risk_score, bool):
        raise TypeError(f"Risk score must be a numeric value, got {type(risk_score).__name__}")

    if not isinstance(risk_score, (int, float)):
        raise TypeError(f"Risk score must be a numeric value, got {type(risk_score).__name__}")

    if math.isnan(risk_score) or math.isinf(risk_score):
        raise ValueError("Risk score cannot be NaN or infinite.")

    # Convert/round if float provided
    score = int(round(risk_score))

    if score < 0 or score > 100:
        raise ValueError(f"Risk score must be between 0 and 100, got {score}")

    if score <= ALLOW_THRESHOLD:
        return Decision.ALLOW, RiskLevel.LOW
    elif score <= REVIEW_THRESHOLD:
        return Decision.REVIEW, RiskLevel.MEDIUM
    else:
        return Decision.BLOCK, RiskLevel.HIGH
