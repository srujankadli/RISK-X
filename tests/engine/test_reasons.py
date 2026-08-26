import pytest
from app.engine.reasons import extract_risk_reasons


class TestExplainabilityReasonExtractor:
    """Tests explainable risk signal extraction from observable transaction inputs."""

    def test_amount_anomaly_signal(self):
        """Verify amount spike generates appropriate risk reason."""
        tx = {"amount": 15000.0, "customer_avg_amount": 2000.0}
        reasons = extract_risk_reasons(tx)
        assert len(reasons) == 1
        assert "Risk signal: transaction amount is significantly above" in reasons[0]
        assert "7.5x higher" in reasons[0]

    def test_velocity_spike_signal(self):
        """Verify rapid transaction bursts trigger velocity reason."""
        tx = {"transactions_last_10min": 3, "transactions_last_1hr": 4}
        reasons = extract_risk_reasons(tx)
        assert len(reasons) == 1
        assert "Risk signal: high transaction velocity detected (3 payments in the last 10 minutes)" in reasons[0]

    def test_elevated_hourly_velocity_signal(self):
        """Verify elevated 1-hour velocity triggers elevated velocity reason."""
        tx = {"transactions_last_10min": 1, "transactions_last_1hr": 4}
        reasons = extract_risk_reasons(tx)
        assert len(reasons) == 1
        assert "Risk signal: elevated transaction velocity detected (4 payments in the last hour)" in reasons[0]

    def test_failed_attempts_signal(self):
        """Verify failed payment retries trigger failed attempts reason."""
        tx = {"failed_attempts": 3}
        reasons = extract_risk_reasons(tx)
        assert len(reasons) == 1
        assert "Risk signal: multiple failed payment attempts detected (3 failed attempts" in reasons[0]

    def test_single_failed_attempt_signal(self):
        """Verify single failed attempt triggers prior failed attempt reason."""
        tx = {"failed_attempts": 1}
        reasons = extract_risk_reasons(tx)
        assert len(reasons) == 1
        assert "Risk signal: previous failed payment attempt recorded" in reasons[0]

    def test_new_device_signal(self):
        """Verify new/unrecognized device triggers new device reason."""
        tx = {"is_new_device": 1}
        reasons = extract_risk_reasons(tx)
        assert len(reasons) == 1
        assert "Risk signal: payment initiated from an unrecognized/new device." in reasons[0]

    def test_multi_account_device_signal(self):
        """Verify device shared across multiple accounts triggers multi-account reason."""
        tx = {"device_account_count": 4}
        reasons = extract_risk_reasons(tx)
        assert len(reasons) == 1
        assert "Risk signal: device is associated with multiple customer accounts (4 accounts observed)." in reasons[0]

    def test_unusual_location_and_time_signals(self):
        """Verify unusual geography and time triggers individual reasons."""
        tx = {"is_unusual_location": 1, "is_unusual_time": 1}
        reasons = extract_risk_reasons(tx)
        assert len(reasons) == 2
        assert any("unusual transaction location" in r for r in reasons)
        assert any("atypical customer activity hours" in r for r in reasons)

    def test_multiple_simultaneous_signals(self):
        """Verify combined attack profile triggers all relevant risk signals."""
        tx = {
            "amount": 25000.0,
            "customer_avg_amount": 1000.0,
            "transactions_last_10min": 3,
            "failed_attempts": 2,
            "is_new_device": 1,
            "device_account_count": 5,
            "is_unusual_location": 1,
            "is_unusual_time": 1,
        }
        reasons = extract_risk_reasons(tx)
        assert len(reasons) == 7
        for r in reasons:
            assert r.startswith("Risk signal: ")

    def test_empty_no_risk_signal_case(self):
        """Verify benign transaction with standard baseline features returns empty reasons list."""
        benign_tx = {
            "amount": 500.0,
            "customer_avg_amount": 600.0,
            "transactions_last_10min": 0,
            "transactions_last_1hr": 0,
            "failed_attempts": 0,
            "is_new_device": 0,
            "device_account_count": 1,
            "is_unusual_location": 0,
            "is_unusual_time": 0,
        }
        reasons = extract_risk_reasons(benign_tx)
        assert reasons == []

    def test_deterministic_reason_extraction(self):
        """Verify identical transaction payload generates identical reasons deterministically."""
        tx = {"amount": 10000.0, "customer_avg_amount": 1000.0, "is_new_device": 1}
        for _ in range(50):
            assert extract_risk_reasons(tx) == extract_risk_reasons(tx)
