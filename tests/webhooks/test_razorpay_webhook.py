"""Integration tests for Razorpay Webhook Ingestion, Signature Verification, and Idempotency."""

import hashlib
import hmac
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def generate_signature(payload_bytes: bytes, secret: str = settings.RAZORPAY_WEBHOOK_SECRET) -> str:
    """Helper to generate valid HMAC-SHA256 signature."""
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


class TestRazorpayWebhookIngestion:
    """Test suite for Razorpay webhook ingestion endpoint."""

    def test_valid_webhook_signature_and_assessment(self, client: TestClient):
        payload = {
            "entity": "event",
            "account_id": "acc_buildathon_01",
            "event": "payment.authorized",
            "contains": ["payment"],
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test_webhook_001",
                        "amount": 280000,  # 280000 paise = INR 2800.00
                        "currency": "INR",
                        "status": "authorized",
                        "method": "card",
                        "notes": {
                            "customer_id": "cust_hook_101",
                            "customer_avg_amount": "1000.0",
                            "account_age_days": "100",
                            "previous_transaction_count": "12",
                            "failed_attempts": "1",
                            "is_new_device": "1",
                            "is_unusual_time": "1",
                        },
                    }
                }
            },
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        sig = generate_signature(body_bytes)

        response = client.post(
            "/api/v1/webhooks/razorpay",
            content=body_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": sig,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
        assert data["payment_id"] == "pay_test_webhook_001"
        assert data["amount_inr"] == 2800.0
        assert data["idempotent_replay"] is False
        assert data["decision"] in ["ALLOW", "REVIEW", "BLOCK"]
        assert 0 <= data["risk_score"] <= 100
        assert 0.0 <= data["fraud_probability"] <= 1.0
        assert isinstance(data["evidence"], list)

    def test_missing_signature_returns_401(self, client: TestClient):
        payload = {"event": "payment.authorized", "id": "pay_no_sig"}
        response = client.post(
            "/api/v1/webhooks/razorpay",
            json=payload,
        )
        assert response.status_code == 401
        assert "signature" in response.json()["detail"].lower()

    def test_invalid_signature_returns_401(self, client: TestClient):
        body_bytes = json.dumps({"event": "payment.authorized"}).encode("utf-8")
        response = client.post(
            "/api/v1/webhooks/razorpay",
            content=body_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": "invalid_fake_hex_signature_12345",
            },
        )
        assert response.status_code == 401
        assert "signature" in response.json()["detail"].lower()

    def test_webhook_idempotency_deduplication(self, client: TestClient):
        payload = {
            "event": "payment.authorized",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_idemp_test_999",
                        "amount": 50000,  # INR 500.00
                        "method": "upi",
                        "notes": {
                            "customer_id": "cust_idemp_01",
                            "customer_avg_amount": "500.0",
                        },
                    }
                }
            },
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        sig = generate_signature(body_bytes)

        # First request -> processed
        res1 = client.post(
            "/api/v1/webhooks/razorpay",
            content=body_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": sig,
            },
        )
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["status"] == "processed"
        assert data1["idempotent_replay"] is False

        # Second request with same payment_id -> idempotent replay without re-scoring
        res2 = client.post(
            "/api/v1/webhooks/razorpay",
            content=body_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": sig,
            },
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["status"] == "idempotent_replay"
        assert data2["idempotent_replay"] is True
        assert data2["risk_score"] == data1["risk_score"]
        assert data2["decision"] == data1["decision"]
