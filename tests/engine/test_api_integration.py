import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestRiskAssessmentAPIIntegration:
    """End-to-end integration tests for the /api/v1/risk/assess endpoint."""

    def test_root_and_health_endpoints_still_operational(self):
        """Verify core health and root endpoints continue to function."""
        health_resp = client.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "healthy"

        root_resp = client.get("/")
        assert root_resp.status_code == 200
        assert "api_v1" in root_resp.json()

    def test_assess_low_risk_legitimate_transaction(self):
        """Verify benign transaction yields ALLOW decision and LOW risk level."""
        payload = {
            "transaction_id": "txn_test_001",
            "customer_id": "cust_test_001",
            "amount": 250.0,
            "payment_method": "upi",
            "account_age_days": 300,
            "previous_transaction_count": 25,
            "failed_attempts": 0,
            "refund_count": 0,
            "customer_avg_amount": 300.0,
            "transactions_last_10min": 0,
            "transactions_last_1hr": 0,
            "device_account_count": 1,
            "is_new_device": 0,
            "is_unusual_time": 0,
            "is_unusual_location": 0,
        }
        response = client.post("/api/v1/risk/assess", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert "risk_score" in data
        assert "fraud_probability" in data
        assert "decision" in data
        assert "risk_level" in data
        assert "reasons" in data

        assert 0 <= data["risk_score"] <= 39
        assert data["decision"] == "ALLOW"
        assert data["risk_level"] == "LOW"
        assert data["transaction_id"] == "txn_test_001"

    def test_assess_high_risk_suspicious_transaction(self):
        """Verify suspicious burst transaction yields BLOCK or REVIEW with explainable signals."""
        payload = {
            "transaction_id": "txn_test_002",
            "customer_id": "cust_test_002",
            "amount": 45000.0,
            "payment_method": "card",
            "account_age_days": 10,
            "previous_transaction_count": 0,
            "failed_attempts": 3,
            "refund_count": 0,
            "customer_avg_amount": 1000.0,
            "transactions_last_10min": 3,
            "transactions_last_1hr": 4,
            "device_account_count": 4,
            "is_new_device": 1,
            "is_unusual_time": 1,
            "is_unusual_location": 1,
        }
        response = client.post("/api/v1/risk/assess", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["risk_score"] >= 40
        assert data["decision"] in ["REVIEW", "BLOCK"]
        assert data["risk_level"] in ["MEDIUM", "HIGH"]
        assert len(data["reasons"]) >= 4
        for reason in data["reasons"]:
            assert reason.startswith("Risk signal: ")

    def test_invalid_transaction_payload_validation_error(self):
        """Verify 422 Unprocessable Entity for invalid data (e.g. negative amount)."""
        payload = {
            "amount": -50.0,  # Invalid: amount must be > 0
            "payment_method": "upi",
        }
        response = client.post("/api/v1/risk/assess", json=payload)
        assert response.status_code == 422
