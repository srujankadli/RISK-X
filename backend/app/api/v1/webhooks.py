"""Razorpay Webhook Ingestion Router."""

import hashlib
import hmac
import json
from typing import Any, Dict, Optional
from fastapi import APIRouter, Header, HTTPException, Request, status
from app.core.config import settings
from app.db.repository import get_transaction_repository
from app.engine.service import risk_service
from app.schemas.webhook import WebhookAssessmentResponse

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def verify_razorpay_signature(raw_body: bytes, signature: Optional[str], secret: str) -> bool:
    """Verify HMAC SHA256 signature for incoming Razorpay webhook event."""
    if not signature or not secret:
        return False
    computed_signature = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(computed_signature, signature)


@router.post(
    "/razorpay",
    response_model=WebhookAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest and assess Razorpay payment webhook event",
    description=(
        "Ingests Razorpay webhook events (e.g. payment.authorized) with HMAC-SHA256 signature "
        "verification and idempotency deduplication. Evaluates payment risk via the ML pipeline "
        "and persists the assessment into the transaction ledger."
    ),
)
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
) -> WebhookAssessmentResponse:
    """Ingest, verify signature, deduplicate, and score Razorpay webhook transaction."""
    raw_body = await request.body()

    # Step 1: Verify HMAC SHA256 Signature
    if not verify_razorpay_signature(raw_body, x_razorpay_signature, settings.RAZORPAY_WEBHOOK_SECRET):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Razorpay webhook signature (X-Razorpay-Signature).",
        )

    # Step 2: Parse Webhook JSON Payload
    try:
        data = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed JSON payload in webhook: {str(e)}",
        )

    event_type = data.get("event", "payment.authorized")
    payload_wrapper = data.get("payload", {})
    payment_obj = payload_wrapper.get("payment", {}).get("entity", {})

    # If payload is flat or passed directly
    if not payment_obj and "amount" in data:
        payment_obj = data

    payment_id = payment_obj.get("id") or data.get("id") or f"pay_unknown_{hashlib.md5(raw_body).hexdigest()[:8]}"

    # Step 3: Idempotency Check
    repo = get_transaction_repository()
    existing_record = repo.get_transaction_by_idempotency_key(payment_id)
    if not existing_record:
        existing_record = repo.get_transaction_by_id(payment_id)

    if existing_record:
        # Return previously evaluated assessment idempotently without duplicate scoring
        return WebhookAssessmentResponse(
            status="idempotent_replay",
            event=event_type,
            payment_id=payment_id,
            transaction_id=existing_record["transaction_id"],
            amount_inr=existing_record["amount"],
            decision=existing_record["decision"],
            risk_score=existing_record["risk_score"],
            risk_level=existing_record["risk_level"],
            fraud_probability=existing_record["fraud_probability"],
            idempotent_replay=True,
            reasons=existing_record.get("reasons", []),
            evidence=existing_record.get("evidence", []),
            analyst_summary=existing_record.get("analyst_summary"),
        )

    # Step 4: Extract Observable Features from Payment Entity & Notes
    # Razorpay amount is in paise (smallest currency unit): 100 paise = 1 INR
    raw_amount = payment_obj.get("amount", 0)
    if isinstance(raw_amount, (int, float)) and raw_amount > 0:
        # Check if already INR or paise
        amount_inr = round(float(raw_amount) / 100.0, 2) if raw_amount >= 100 else float(raw_amount)
    else:
        amount_inr = 100.0

    notes = payment_obj.get("notes", {})
    if not isinstance(notes, dict):
        notes = {}

    def _get_note_val(key: str, default: Any, val_type=int):
        raw = notes.get(key)
        if raw is None:
            return default
        try:
            return val_type(raw)
        except (ValueError, TypeError):
            return default

    # Map payment method
    method_raw = str(payment_obj.get("method", "card")).lower()
    valid_methods = {"card", "upi", "netbanking", "wallet"}
    payment_method = method_raw if method_raw in valid_methods else "card"

    transaction_request = {
        "amount": amount_inr,
        "customer_avg_amount": _get_note_val("customer_avg_amount", amount_inr, float),
        "payment_method": payment_method,
        "account_age_days": _get_note_val("account_age_days", 30, int),
        "previous_transaction_count": _get_note_val("previous_transaction_count", 5, int),
        "failed_attempts": _get_note_val("failed_attempts", 0, int),
        "refund_count": _get_note_val("refund_count", 0, int),
        "transactions_last_10min": _get_note_val("transactions_last_10min", 0, int),
        "transactions_last_1hr": _get_note_val("transactions_last_1hr", 0, int),
        "device_account_count": _get_note_val("device_account_count", 1, int),
        "is_new_device": _get_note_val("is_new_device", 0, int),
        "is_unusual_time": _get_note_val("is_unusual_time", 0, int),
        "is_unusual_location": _get_note_val("is_unusual_location", 0, int),
        "transaction_id": payment_id,
        "customer_id": notes.get("customer_id") or payment_obj.get("email") or payment_obj.get("contact"),
    }

    # Step 5: Execute Real Risk Assessment and Persist with Idempotency Key
    assessment = risk_service.assess_transaction(
        transaction=transaction_request,
        persist=True,
        source="webhook",
        idempotency_key=payment_id,
    )

    return WebhookAssessmentResponse(
        status="processed",
        event=event_type,
        payment_id=payment_id,
        transaction_id=assessment.transaction_id or payment_id,
        amount_inr=amount_inr,
        decision=assessment.decision,
        risk_score=assessment.risk_score,
        risk_level=assessment.risk_level,
        fraud_probability=assessment.fraud_probability,
        idempotent_replay=False,
        reasons=assessment.reasons,
        evidence=assessment.evidence,
        analyst_summary=assessment.analyst_summary,
    )
