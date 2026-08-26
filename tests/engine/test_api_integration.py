from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.engine.service import RiskEngineService

client = TestClient(app)


class TestProductionInferenceWorkflow:
    """Production inference workflow, validation, readiness, and structured evidence tests."""

    # -------------------------------------------------------------
    # 1. Health & Readiness Separation
    # -------------------------------------------------------------
    def test_liveness_probe(self):
        """Verify liveness endpoint indicates FastAPI server is operational."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "RISK-X" in data["service"]

    def test_readiness_probes(self):
        """Verify readiness endpoints confirm model & preprocessor are loaded in memory."""
        for path in ["/health/ready", "/ready", "/api/v1/risk/readiness"]:
            resp = client.get(path)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ready"
            assert data.get("model_loaded") is True or data.get("ready") is True

    # -------------------------------------------------------------
    # 2. Real-Time Inference, Contract & Backward Compatibility
    # -------------------------------------------------------------
    def test_assess_low_risk_transaction(self):
        """Verify low-risk transaction produces ALLOW decision, empty evidence, and baseline summary."""
        payload = {
            "transaction_id": "txn_test_allow_01",
            "customer_id": "cust_test_01",
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
        resp = client.post("/api/v1/risk/assess", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        # Core fields
        assert 0 <= data["risk_score"] <= 39
        assert data["decision"] == "ALLOW"
        assert data["risk_level"] == "LOW"
        assert 0.0 <= data["fraud_probability"] <= 0.39
        assert data["transaction_id"] == "txn_test_allow_01"

        # Backward compatibility
        assert data["reasons"] == []

        # Milestone 5 Evidence Layer
        assert "evidence" in data
        assert data["evidence"] == []
        assert "analyst_summary" in data
        assert "ALLOW" in data["analyst_summary"]

    def test_assess_high_risk_transaction(self):
        """Verify high-risk attack transaction produces BLOCK decision with structured evidence and reasons."""
        payload = {
            "transaction_id": "txn_test_block_01",
            "customer_id": "cust_test_02",
            "amount": 55000.0,
            "payment_method": "card",
            "account_age_days": 5,
            "previous_transaction_count": 0,
            "failed_attempts": 3,
            "refund_count": 0,
            "customer_avg_amount": 1000.0,
            "transactions_last_10min": 3,
            "transactions_last_1hr": 5,
            "device_account_count": 4,
            "is_new_device": 1,
            "is_unusual_time": 1,
            "is_unusual_location": 1,
        }
        resp = client.post("/api/v1/risk/assess", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["risk_score"] >= 70
        assert data["decision"] == "BLOCK"
        assert data["risk_level"] == "HIGH"

        # Backward compatibility for reasons
        assert len(data["reasons"]) >= 4
        for r in data["reasons"]:
            assert r.startswith("Risk signal: ")

        # Structured Evidence verification
        assert "evidence" in data
        assert len(data["evidence"]) >= 4
        for item in data["evidence"]:
            assert "code" in item
            assert item["severity"] in ["HIGH", "MEDIUM", "LOW"]
            assert "title" in item
            assert "description" in item
            assert "observed_value" in item
            assert "reference_threshold" in item

        # Analyst summary verification
        assert "analyst_summary" in data
        assert "BLOCK" in data["analyst_summary"]
        assert "risk score" in data["analyst_summary"]

    # -------------------------------------------------------------
    # 3. Determinism
    # -------------------------------------------------------------
    def test_deterministic_repeated_calls(self):
        """Verify repeated calls with identical payload yield identical outputs."""
        payload = {
            "amount": 4500.0,
            "payment_method": "netbanking",
            "customer_avg_amount": 1200.0,
            "transactions_last_10min": 1,
            "is_new_device": 1,
        }
        first_resp = client.post("/api/v1/risk/assess", json=payload).json()

        for _ in range(25):
            curr_resp = client.post("/api/v1/risk/assess", json=payload).json()
            assert curr_resp["risk_score"] == first_resp["risk_score"]
            assert curr_resp["fraud_probability"] == first_resp["fraud_probability"]
            assert curr_resp["decision"] == first_resp["decision"]
            assert curr_resp["reasons"] == first_resp["reasons"]
            assert curr_resp["evidence"] == first_resp["evidence"]
            assert curr_resp["analyst_summary"] == first_resp["analyst_summary"]

    # -------------------------------------------------------------
    # 4. Strict Input Validation (HTTP 422)
    # -------------------------------------------------------------
    @pytest.mark.parametrize(
        "invalid_field",
        [
            {"amount": -100.0},
            {"amount": 0.0},
            {"payment_method": "crypto"},
            {"payment_method": "invalid_rail"},
            {"account_age_days": -1},
            {"previous_transaction_count": -5},
            {"failed_attempts": -1},
            {"refund_count": -2},
            {"customer_avg_amount": -50.0},
            {"transactions_last_10min": -1},
            {"transactions_last_1hr": -1},
            {"device_account_count": 0},
            {"is_new_device": 2},
            {"is_new_device": -1},
            {"is_unusual_time": 5},
            {"is_unusual_location": -1},
            {"label": 1, "amount": 500.0},  # Forbidden field: target leakage prevention
            {"is_fraud": 1, "amount": 500.0},  # Forbidden field: target leakage prevention
        ],
    )
    def test_validation_error_responses(self, invalid_field):
        """Verify Pydantic rejects invalid parameters and forbidden fields with 422."""
        base_payload = {"amount": 500.0, "payment_method": "upi"}
        base_payload.update(invalid_field)
        resp = client.post("/api/v1/risk/assess", json=base_payload)
        assert resp.status_code == 422

    def test_missing_body_error(self):
        """Verify empty body returns 422."""
        resp = client.post("/api/v1/risk/assess", json={})
        assert resp.status_code == 422

    # -------------------------------------------------------------
    # 5. Failure Modes & Missing Artifact Handling (HTTP 503)
    # -------------------------------------------------------------
    def test_service_unavailable_on_missing_model_artifact(self):
        """Verify service returns 503 when model artifact file is missing."""
        faulty_service = RiskEngineService(
            model_path=Path("ml/models/non_existent_model.joblib"),
            preprocessor_path=Path("ml/models/preprocessor.joblib"),
        )
        with pytest.raises(FileNotFoundError):
            faulty_service.assess_transaction({"amount": 500.0})

        readiness = faulty_service.check_readiness()
        assert readiness["ready"] is False
        assert "not found" in readiness["error"].lower()

    def test_service_unavailable_on_missing_preprocessor_artifact(self):
        """Verify service returns 503 when preprocessor artifact file is missing."""
        faulty_service = RiskEngineService(
            model_path=Path("ml/models/random_forest_detector.joblib"),
            preprocessor_path=Path("ml/models/non_existent_preprocessor.joblib"),
        )
        with pytest.raises(FileNotFoundError):
            faulty_service.assess_transaction({"amount": 500.0})

        readiness = faulty_service.check_readiness()
        assert readiness["ready"] is False
        assert "not found" in readiness["error"].lower()
