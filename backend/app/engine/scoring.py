"""
RISK-X Risk Scoring Module
==========================
Converts Random Forest predicted fraud probability into a deterministic 0-100 risk score.
"""

import math
from typing import Union


def calculate_risk_score(fraud_probability: Union[float, int]) -> int:
    """
    Converts a model-predicted fraud probability in [0.0, 1.0] into a deterministic integer
    risk score in the range [0, 100].

    Mapping Formula:
        risk_score = round(fraud_probability * 100)

    Validation Rules:
        - Must be a finite real number (float or int).
        - Must fall within the closed interval [0.0, 1.0].
        - Slight floating-point inaccuracies (e.g. 1.0000000000000002 or -1e-15) are clamped safely.
        - NaN, Infinite, Negative, or Out-of-bounds (> 1.0) values raise ValueError.

    Args:
        fraud_probability: Model-predicted probability of fraudulent activity, in [0.0, 1.0].

    Returns:
        Deterministic integer risk score between 0 and 100.

    Raises:
        TypeError: If fraud_probability is not a float or integer.
        ValueError: If fraud_probability is NaN, infinite, or outside [0.0, 1.0].
    """
    if fraud_probability is None or isinstance(fraud_probability, bool):
        raise TypeError(f"Fraud probability must be a float or integer, got {type(fraud_probability).__name__}")

    if not isinstance(fraud_probability, (int, float)):
        raise TypeError(f"Fraud probability must be a float or integer, got {type(fraud_probability).__name__}")

    if math.isnan(fraud_probability):
        raise ValueError("Fraud probability cannot be NaN.")

    if math.isinf(fraud_probability):
        raise ValueError("Fraud probability cannot be infinite.")

    # Numerical tolerance for floating-point imprecision
    FLOAT_TOLERANCE = 1e-9

    if fraud_probability < -FLOAT_TOLERANCE or fraud_probability > (1.0 + FLOAT_TOLERANCE):
        raise ValueError(
            f"Fraud probability out of valid range [0.0, 1.0]: got {fraud_probability}"
        )

    # Clamp minor floating-point drift safely to [0.0, 1.0]
    clamped_prob = max(0.0, min(1.0, float(fraud_probability)))

    # Transparent mathematical linear mapping: round half-up to integer in [0, 100]
    score = int(math.floor(clamped_prob * 100.0 + 0.5))

    return max(0, min(100, score))
