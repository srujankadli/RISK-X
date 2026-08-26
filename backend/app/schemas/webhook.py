"""Pydantic schemas for Webhook Ingestion, Transaction History, and Risk Statistics."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.risk import EvidenceItem, DecisionEnum, RiskLevelEnum


class RazorpayPaymentEntity(BaseModel):
    """Schema for standard Razorpay payment entity object."""
    id: str = Field(description="Razorpay payment ID, e.g. pay_O7yR9s8E3abc")
    entity: str = Field(default="payment", description="Entity type")
    amount: int = Field(description="Payment amount in paise (smallest currency unit, e.g. 250000 = INR 2,500.00)")
    currency: str = Field(default="INR", description="Payment currency code")
    status: str = Field(default="authorized", description="Payment state")
    method: str = Field(default="card", description="Payment method: card, upi, netbanking, wallet")
    order_id: Optional[str] = Field(default=None, description="Razorpay order ID")
    description: Optional[str] = Field(default=None)
    card_id: Optional[str] = Field(default=None)
    bank: Optional[str] = Field(default=None)
    wallet: Optional[str] = Field(default=None)
    vpa: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    contact: Optional[str] = Field(default=None)
    notes: Dict[str, Any] = Field(default_factory=dict, description="Metadata key-value pairs associated with transaction")
    created_at: Optional[int] = Field(default=None)

    model_config = ConfigDict(extra="ignore")


class RazorpayWebhookPayload(BaseModel):
    """Schema for incoming Razorpay webhook event payload."""
    entity: str = Field(default="event", description="Webhook entity type")
    account_id: Optional[str] = Field(default=None, description="Merchant merchant account ID")
    event: str = Field(description="Razorpay webhook event type, e.g. payment.authorized")
    contains: List[str] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(description="Entity wrapper payload containing payment object")
    created_at: Optional[int] = Field(default=None)

    model_config = ConfigDict(extra="ignore")


class WebhookAssessmentResponse(BaseModel):
    """Response returned upon processing a Razorpay webhook event."""
    status: str = Field(description="Processing outcome: processed, idempotent_replay, ignored")
    event: str = Field(description="Webhook event type")
    payment_id: str = Field(description="Razorpay payment identifier")
    transaction_id: str = Field(description="Assessed transaction reference ID")
    amount_inr: float = Field(description="Transaction amount in INR")
    decision: DecisionEnum = Field(description="Guarded decision action")
    risk_score: int = Field(description="Deterministic integer risk score (0-100)")
    risk_level: RiskLevelEnum = Field(description="Risk level tier: LOW, MEDIUM, HIGH")
    fraud_probability: float = Field(description="Random Forest predicted fraud probability")
    idempotent_replay: bool = Field(default=False, description="True if webhook was already processed and retrieved idempotently")
    reasons: List[str] = Field(default_factory=list, description="Explainable risk reasons")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Structured evidence items")
    analyst_summary: Optional[str] = Field(default=None, description="Narrative summary for analyst")

    model_config = ConfigDict(extra="forbid")


class TransactionHistoryItem(BaseModel):
    """Schema representing an individual transaction record in history."""
    id: int
    transaction_id: str
    customer_id: Optional[str] = None
    merchant_id: Optional[str] = None
    amount: float
    customer_avg_amount: float
    payment_method: str
    risk_score: int
    fraud_probability: float
    decision: DecisionEnum
    risk_level: RiskLevelEnum
    source: str
    idempotency_key: Optional[str] = None
    created_at: str
    reasons: List[str] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    analyst_summary: Optional[str] = None
    raw_request: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="ignore")


class TransactionHistoryResponse(BaseModel):
    """Paginated list of transactions in historical ledger."""
    items: List[TransactionHistoryItem]
    total: int
    limit: int
    offset: int

    model_config = ConfigDict(extra="forbid")


class RiskStatsResponse(BaseModel):
    """Aggregated risk overview statistics."""
    total_transactions: int
    allow_count: int
    review_count: int
    block_count: int
    allow_rate: float
    review_rate: float
    block_rate: float
    average_risk_score: float
    average_fraud_probability: float

    model_config = ConfigDict(extra="forbid")
