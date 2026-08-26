"""
RISK-X Structured Evidence & Explainability Engine
==================================================
Extracts structured, ranked, analyst-facing evidence signals from observable
transaction-time attributes without exposing model internals or target labels.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class EvidenceSeverity(str, Enum):
    """Severity tier for an individual risk signal."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EvidenceSignalCode(str, Enum):
    """Standardized machine-readable evidence signal codes."""
    AMOUNT_SPIKE = "AMOUNT_SPIKE"
    VELOCITY_BURST_10MIN = "VELOCITY_BURST_10MIN"
    VELOCITY_ELEVATED_1HR = "VELOCITY_ELEVATED_1HR"
    FAILED_ATTEMPTS_BURST = "FAILED_ATTEMPTS_BURST"
    FAILED_ATTEMPT_PRIOR = "FAILED_ATTEMPT_PRIOR"
    NEW_DEVICE = "NEW_DEVICE"
    DEVICE_MULTI_ACCOUNT_REUSE = "DEVICE_MULTI_ACCOUNT_REUSE"
    UNUSUAL_LOCATION = "UNUSUAL_LOCATION"
    UNUSUAL_TIME = "UNUSUAL_TIME"


class EvidenceItem(BaseModel):
    """Structured observable evidence signal for analyst review."""
    code: str = Field(..., description="Standardized machine-readable signal code")
    severity: EvidenceSeverity = Field(..., description="Signal severity: HIGH, MEDIUM, LOW")
    title: str = Field(..., description="Concise human-readable signal title")
    description: str = Field(..., description="Detailed explainable description of observed indicator")
    observed_value: Any = Field(..., description="Observed transaction metric value")
    reference_threshold: Optional[str] = Field(
        default=None,
        description="Reference baseline or threshold criteria applied"
    )


# Severity numerical weight for deterministic sorting (higher = more severe)
SEVERITY_WEIGHTS = {
    EvidenceSeverity.HIGH: 3,
    EvidenceSeverity.MEDIUM: 2,
    EvidenceSeverity.LOW: 1,
}


def extract_structured_evidence(
    transaction_data: Union[Dict[str, Any], Any]
) -> List[EvidenceItem]:
    """
    Extracts structured, observable risk evidence signals and ranks them
    deterministically by severity and signal priority.

    Args:
        transaction_data: Dictionary or Pydantic object containing observable transaction features.

    Returns:
        List[EvidenceItem]: Deterministically ordered list of structured evidence items.
    """
    if hasattr(transaction_data, "model_dump"):
        data = transaction_data.model_dump()
    elif hasattr(transaction_data, "__dict__") and not isinstance(transaction_data, dict):
        data = transaction_data.__dict__
    elif isinstance(transaction_data, dict):
        data = transaction_data
    else:
        data = {}

    evidence_list: List[EvidenceItem] = []

    # 1. Amount Anomaly
    amount = float(data.get("amount", 0.0) or 0.0)
    customer_avg = float(data.get("customer_avg_amount", 0.0) or 0.0)
    if customer_avg > 0 and amount >= (3.0 * customer_avg):
        ratio = amount / customer_avg
        severity = EvidenceSeverity.HIGH if ratio >= 5.0 else EvidenceSeverity.MEDIUM
        evidence_list.append(
            EvidenceItem(
                code=EvidenceSignalCode.AMOUNT_SPIKE.value,
                severity=severity,
                title="Unusual Transaction Amount Spike",
                description=(
                    f"Transaction amount of INR {amount:,.2f} is significantly above customer "
                    f"historical average of INR {customer_avg:,.2f} ({ratio:.1f}x baseline)."
                ),
                observed_value=round(amount, 2),
                reference_threshold=f">= 3.0x customer average (INR {customer_avg:,.2f})",
            )
        )

    # 2. Velocity Burst (10 min)
    tx_10min = int(data.get("transactions_last_10min", 0) or 0)
    tx_1hr = int(data.get("transactions_last_1hr", 0) or 0)
    if tx_10min >= 2:
        severity = EvidenceSeverity.HIGH if tx_10min >= 3 else EvidenceSeverity.MEDIUM
        evidence_list.append(
            EvidenceItem(
                code=EvidenceSignalCode.VELOCITY_BURST_10MIN.value,
                severity=severity,
                title="Rapid Payment Velocity (10 min)",
                description=f"High frequency of {tx_10min} payment attempts recorded in the past 10 minutes.",
                observed_value=tx_10min,
                reference_threshold=">= 2 transactions in 10 minutes",
            )
        )
    elif tx_10min == 1 and tx_1hr >= 3:
        evidence_list.append(
            EvidenceItem(
                code=EvidenceSignalCode.VELOCITY_ELEVATED_1HR.value,
                severity=EvidenceSeverity.MEDIUM,
                title="Elevated Hourly Payment Velocity",
                description=f"Elevated velocity of {tx_1hr} payment attempts recorded across the past 1 hour.",
                observed_value=tx_1hr,
                reference_threshold=">= 3 transactions in 1 hour",
            )
        )

    # 3. Failed Payment Attempts
    failed_attempts = int(data.get("failed_attempts", 0) or 0)
    if failed_attempts >= 2:
        severity = EvidenceSeverity.HIGH if failed_attempts >= 3 else EvidenceSeverity.MEDIUM
        evidence_list.append(
            EvidenceItem(
                code=EvidenceSignalCode.FAILED_ATTEMPTS_BURST.value,
                severity=severity,
                title="Multiple Failed Payment Retries",
                description=f"{failed_attempts} failed payment attempts recorded immediately prior to this transaction.",
                observed_value=failed_attempts,
                reference_threshold=">= 2 failed authorization attempts",
            )
        )
    elif failed_attempts == 1:
        evidence_list.append(
            EvidenceItem(
                code=EvidenceSignalCode.FAILED_ATTEMPT_PRIOR.value,
                severity=EvidenceSeverity.LOW,
                title="Previous Failed Payment Attempt",
                description="1 failed payment attempt recorded prior to authorization.",
                observed_value=1,
                reference_threshold="1 failed authorization attempt",
            )
        )

    # 4. New / Unrecognized Device
    is_new_device = int(data.get("is_new_device", 0) or 0)
    if is_new_device == 1:
        evidence_list.append(
            EvidenceItem(
                code=EvidenceSignalCode.NEW_DEVICE.value,
                severity=EvidenceSeverity.MEDIUM,
                title="Unrecognized Device Fingerprint",
                description="Payment initiated from a previously unseen device fingerprint for this customer account.",
                observed_value=1,
                reference_threshold="Device first observed = 1",
            )
        )

    # 5. Multi-Account Device Reuse
    device_account_count = int(data.get("device_account_count", 1) or 1)
    if device_account_count >= 2:
        severity = EvidenceSeverity.HIGH if device_account_count >= 3 else EvidenceSeverity.MEDIUM
        evidence_list.append(
            EvidenceItem(
                code=EvidenceSignalCode.DEVICE_MULTI_ACCOUNT_REUSE.value,
                severity=severity,
                title="Multi-Account Device Association",
                description=f"Device hardware fingerprint has been associated with {device_account_count} distinct customer accounts.",
                observed_value=device_account_count,
                reference_threshold=">= 2 associated accounts",
            )
        )

    # 6. Unusual Location Anomaly
    is_unusual_location = int(data.get("is_unusual_location", 0) or 0)
    if is_unusual_location == 1:
        evidence_list.append(
            EvidenceItem(
                code=EvidenceSignalCode.UNUSUAL_LOCATION.value,
                severity=EvidenceSeverity.MEDIUM,
                title="Atypical Geographic Location",
                description="Transaction origin city/region deviates from customer historical operating territory.",
                observed_value=1,
                reference_threshold="Unusual location flag = 1",
            )
        )

    # 7. Unusual Time Anomaly
    is_unusual_time = int(data.get("is_unusual_time", 0) or 0)
    if is_unusual_time == 1:
        evidence_list.append(
            EvidenceItem(
                code=EvidenceSignalCode.UNUSUAL_TIME.value,
                severity=EvidenceSeverity.LOW,
                title="Off-Hours Transaction Activity",
                description="Transaction initiated outside established customer active operating hours.",
                observed_value=1,
                reference_threshold="Unusual time flag = 1",
            )
        )

    # Deterministic sorting:
    # 1. Primary: Severity weight (HIGH=3, MEDIUM=2, LOW=1) descending
    # 2. Secondary: Signal code string ascending for stable idempotency
    evidence_list.sort(
        key=lambda item: (-SEVERITY_WEIGHTS[item.severity], item.code)
    )

    return evidence_list


def generate_analyst_summary(
    evidence: List[EvidenceItem],
    decision: str,
    risk_score: int,
) -> str:
    """
    Generates a concise, structured narrative summary tailored for risk analysts.

    Args:
        evidence: List of structured EvidenceItem objects.
        decision: Decision policy action (ALLOW, REVIEW, BLOCK).
        risk_score: Deterministic integer risk score in [0, 100].

    Returns:
        str: Concise analyst-facing explanation.
    """
    if not evidence:
        return (
            f"Transaction evaluated with low risk score {risk_score} ({decision}). "
            "All observable attributes conform to standard customer baselines with no elevated risk signals."
        )

    high_count = sum(1 for e in evidence if e.severity == EvidenceSeverity.HIGH)
    med_count = sum(1 for e in evidence if e.severity == EvidenceSeverity.MEDIUM)
    low_count = sum(1 for e in evidence if e.severity == EvidenceSeverity.LOW)

    top_signals = [e.title.lower() for e in evidence[:3]]
    signals_str = ", ".join(top_signals)

    severity_desc = []
    if high_count > 0:
        severity_desc.append(f"{high_count} high-severity")
    if med_count > 0:
        severity_desc.append(f"{med_count} medium-severity")
    if low_count > 0:
        severity_desc.append(f"{low_count} low-severity")

    counts_str = " and ".join(severity_desc) if len(severity_desc) <= 2 else f"{', '.join(severity_desc[:-1])}, and {severity_desc[-1]}"

    return (
        f"Transaction evaluated with risk score {risk_score} triggering policy {decision}. "
        f"Detected {len(evidence)} risk signals ({counts_str}) driven primarily by {signals_str}."
    )
