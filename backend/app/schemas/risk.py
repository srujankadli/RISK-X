"""
RISK-X Risk Assessment Pydantic Contracts
=========================================
Defines input transaction assessment requests and deterministic risk evaluation responses.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


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


class TransactionAssessmentRequest(BaseModel):
    """Observable transaction payload submitted for real-time risk assessment."""
    amount: float = Field(..., gt=0, description="Transaction amount in INR (must be > 0)")
    payment_method: str = Field(default="upi", description="Payment method: upi, card, netbanking, wallet")
    account_age_days: int = Field(default=0, ge=0, description="Account age in days at transaction time")
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

    # Optional metadata identifiers for audit tracing (excluded from model features)
    transaction_id: Optional[str] = Field(default=None, description="Unique transaction ID for tracing")
    customer_id: Optional[str] = Field(default=None, description="Customer ID")
    merchant_id: Optional[str] = Field(default=None, description="Merchant ID")
    device_id: Optional[str] = Field(default=None, description="Device fingerprint ID")
    ip_address: Optional[str] = Field(default=None, description="Client IP address")
    timestamp: Optional[str] = Field(default=None, description="Transaction timestamp in ISO 8601")
    location: Optional[str] = Field(default=None, description="Location name or city")


class RiskAssessmentResponse(BaseModel):
    """Deterministic, explainable risk assessment response."""
    risk_score: int = Field(..., ge=0, le=100, description="Deterministic risk score in [0, 100]")
    fraud_probability: float = Field(..., ge=0.0, le=1.0, description="Random Forest predicted fraud probability in [0.0, 1.0]")
    decision: DecisionEnum = Field(..., description="Guarded operational decision: ALLOW, REVIEW, BLOCK")
    risk_level: RiskLevelEnum = Field(..., description="Risk severity tier: LOW, MEDIUM, HIGH")
    reasons: List[str] = Field(default_factory=list, description="Concise explainable risk signals detected")
    transaction_id: Optional[str] = Field(default=None, description="Associated transaction ID if provided")
