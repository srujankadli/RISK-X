"""
RISK-X Risk Assessment Pydantic Contracts
=========================================
Defines input transaction assessment requests and deterministic risk evaluation responses
with backward-compatible structured evidence representations.
"""

from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PaymentMethodEnum(str, Enum):
    """Supported payment rail methods."""
    UPI = "upi"
    CARD = "card"
    NETBANKING = "netbanking"
    WALLET = "wallet"


class DecisionEnum(str, Enum):
    """Guarded operational response for payment transactions."""
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class RiskLevelEnum(str, Enum):
    """Risk severity tier."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class EvidenceSeverityEnum(str, Enum):
    """Severity tier for an individual structured evidence signal."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EvidenceSignalCodeEnum(str, Enum):
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
    severity: EvidenceSeverityEnum = Field(..., description="Signal severity tier: HIGH, MEDIUM, LOW")
    title: str = Field(..., description="Concise human-readable signal title")
    description: str = Field(..., description="Detailed explainable description of observed indicator")
    observed_value: Any = Field(..., description="Observed transaction metric value")
    reference_threshold: Optional[str] = Field(
        default=None,
        description="Reference baseline or threshold criteria applied"
    )


class TransactionAssessmentRequest(BaseModel):
    """
    Observable transaction payload submitted for real-time risk assessment.

    Strict validation is enforced:
    - Extra unexpected fields (e.g. 'label', 'is_fraud') are forbidden to prevent target leakage.
    - Amount must be strictly greater than zero.
    - Counters and ages must be non-negative.
    """
    amount: float = Field(..., gt=0, description="Transaction amount in INR (must be > 0)")
    payment_method: PaymentMethodEnum = Field(
        default=PaymentMethodEnum.UPI,
        description="Payment method rail: upi, card, netbanking, wallet"
    )
    account_age_days: int = Field(default=0, ge=0, le=36500, description="Account age in days at transaction time")
    previous_transaction_count: int = Field(default=0, ge=0, description="Historical successful transactions")
    failed_attempts: int = Field(default=0, ge=0, description="Immediate failed attempts prior to authorization")
    refund_count: int = Field(default=0, ge=0, description="Historical refund count")
    customer_avg_amount: float = Field(default=0.0, ge=0, description="Customer historical average transaction amount")
    transactions_last_10min: int = Field(default=0, ge=0, description="Transactions within the prior 10 minutes")
    transactions_last_1hr: int = Field(default=0, ge=0, description="Transactions within the prior 1 hour")
    device_account_count: int = Field(default=1, ge=1, description="Number of distinct customer accounts seen on device")
    is_new_device: int = Field(default=0, ge=0, le=1, description="1 if unobserved device, else 0")
    is_unusual_time: int = Field(default=0, ge=0, le=1, description="1 if outside active hours, else 0")
    is_unusual_location: int = Field(default=0, ge=0, le=1, description="1 if outside regular locations, else 0")

    # Optional metadata identifiers for audit tracing (excluded from ML features)
    transaction_id: Optional[str] = Field(default=None, description="Unique transaction ID for tracing")
    customer_id: Optional[str] = Field(default=None, description="Customer ID")
    merchant_id: Optional[str] = Field(default=None, description="Merchant ID")
    device_id: Optional[str] = Field(default=None, description="Device fingerprint ID")
    ip_address: Optional[str] = Field(default=None, description="Client IP address")
    timestamp: Optional[str] = Field(default=None, description="Transaction timestamp in ISO 8601")
    location: Optional[str] = Field(default=None, description="Location name or city")

    # Forbid extra fields like 'label' or 'is_fraud' to guarantee zero target leakage
    model_config = ConfigDict(extra="forbid")


class RiskAssessmentResponse(BaseModel):
    """Deterministic, explainable risk assessment response."""
    risk_score: int = Field(..., ge=0, le=100, description="Deterministic risk score in [0, 100]")
    fraud_probability: float = Field(..., ge=0.0, le=1.0, description="Random Forest predicted fraud probability in [0.0, 1.0]")
    decision: DecisionEnum = Field(..., description="Guarded operational decision: ALLOW, REVIEW, BLOCK")
    risk_level: RiskLevelEnum = Field(..., description="Risk severity tier: LOW, MEDIUM, HIGH")
    reasons: List[str] = Field(default_factory=list, description="Concise explainable risk signals detected")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Structured, ranked observable risk evidence items")
    analyst_summary: Optional[str] = Field(default=None, description="Concise narrative summary of risk assessment for analysts")
    transaction_id: Optional[str] = Field(default=None, description="Associated transaction ID if provided")
