import pytest
from app.engine.evidence import (
    extract_structured_evidence,
    generate_analyst_summary,
    EvidenceSeverity,
    EvidenceSignalCode,
    EvidenceItem,
    SEVERITY_WEIGHTS,
)


class TestStructuredEvidenceLayer:
    """Comprehensive tests for observable structured evidence signals and analyst summaries."""

    # -------------------------------------------------------------------------
    # 1. Individual Signal Extraction Tests
    # -------------------------------------------------------------------------
    def test_amount_spike_high_severity(self):
        """Verify >= 5.0x average ratio produces HIGH severity AMOUNT_SPIKE."""
        tx = {"amount": 25000.0, "customer_avg_amount": 2000.0}  # 12.5x
        evidence = extract_structured_evidence(tx)
        assert len(evidence) == 1
        item = evidence[0]
        assert item.code == EvidenceSignalCode.AMOUNT_SPIKE.value
        assert item.severity == EvidenceSeverity.HIGH
        assert "12.5x" in item.description
        assert item.observed_value == 25000.0
        assert ">= 3.0x" in item.reference_threshold

    def test_amount_spike_medium_severity(self):
        """Verify 3.0x - 4.9x ratio produces MEDIUM severity AMOUNT_SPIKE."""
        tx = {"amount": 7000.0, "customer_avg_amount": 2000.0}  # 3.5x
        evidence = extract_structured_evidence(tx)
        assert len(evidence) == 1
        item = evidence[0]
        assert item.code == EvidenceSignalCode.AMOUNT_SPIKE.value
        assert item.severity == EvidenceSeverity.MEDIUM
        assert "3.5x" in item.description

    def test_velocity_burst_10min_high_severity(self):
        """Verify >= 3 payments in 10 minutes produces HIGH severity VELOCITY_BURST_10MIN."""
        tx = {"transactions_last_10min": 4}
        evidence = extract_structured_evidence(tx)
        assert len(evidence) == 1
        item = evidence[0]
        assert item.code == EvidenceSignalCode.VELOCITY_BURST_10MIN.value
        assert item.severity == EvidenceSeverity.HIGH
        assert item.observed_value == 4

    def test_velocity_burst_10min_medium_severity(self):
        """Verify 2 payments in 10 minutes produces MEDIUM severity VELOCITY_BURST_10MIN."""
        tx = {"transactions_last_10min": 2}
        evidence = extract_structured_evidence(tx)
        assert len(evidence) == 1
        item = evidence[0]
        assert item.code == EvidenceSignalCode.VELOCITY_BURST_10MIN.value
        assert item.severity == EvidenceSeverity.MEDIUM
        assert item.observed_value == 2

    def test_velocity_elevated_1hr_medium_severity(self):
        """Verify 1 payment in 10min but >= 3 in 1hr produces VELOCITY_ELEVATED_1HR."""
        tx = {"transactions_last_10min": 1, "transactions_last_1hr": 4}
        evidence = extract_structured_evidence(tx)
        assert len(evidence) == 1
        item = evidence[0]
        assert item.code == EvidenceSignalCode.VELOCITY_ELEVATED_1HR.value
        assert item.severity == EvidenceSeverity.MEDIUM
        assert item.observed_value == 4

    def test_failed_attempts_burst_high_severity(self):
        """Verify >= 3 failed attempts produces HIGH severity FAILED_ATTEMPTS_BURST."""
        tx = {"failed_attempts": 3}
        evidence = extract_structured_evidence(tx)
        assert len(evidence) == 1
        item = evidence[0]
        assert item.code == EvidenceSignalCode.FAILED_ATTEMPTS_BURST.value
        assert item.severity == EvidenceSeverity.HIGH
        assert item.observed_value == 3

    def test_failed_attempts_burst_medium_severity(self):
        """Verify 2 failed attempts produces MEDIUM severity FAILED_ATTEMPTS_BURST."""
        tx = {"failed_attempts": 2}
        evidence = extract_structured_evidence(tx)
        assert len(evidence) == 1
        item = evidence[0]
        assert item.code == EvidenceSignalCode.FAILED_ATTEMPTS_BURST.value
        assert item.severity == EvidenceSeverity.MEDIUM
        assert item.observed_value == 2

    def test_failed_attempt_prior_low_severity(self):
        """Verify 1 failed attempt produces LOW severity FAILED_ATTEMPT_PRIOR."""
        tx = {"failed_attempts": 1}
        evidence = extract_structured_evidence(tx)
        assert len(evidence) == 1
        item = evidence[0]
        assert item.code == EvidenceSignalCode.FAILED_ATTEMPT_PRIOR.value
        assert item.severity == EvidenceSeverity.LOW
        assert item.observed_value == 1

    def test_new_device_signal(self):
        """Verify new device produces MEDIUM severity NEW_DEVICE."""
        tx = {"is_new_device": 1}
        evidence = extract_structured_evidence(tx)
        assert len(evidence) == 1
        item = evidence[0]
        assert item.code == EvidenceSignalCode.NEW_DEVICE.value
        assert item.severity == EvidenceSeverity.MEDIUM

    def test_device_multi_account_reuse_high_severity(self):
        """Verify >= 3 accounts on device produces HIGH severity DEVICE_MULTI_ACCOUNT_REUSE."""
        tx = {"device_account_count": 5}
        evidence = extract_structured_evidence(tx)
        assert len(evidence) == 1
        item = evidence[0]
        assert item.code == EvidenceSignalCode.DEVICE_MULTI_ACCOUNT_REUSE.value
        assert item.severity == EvidenceSeverity.HIGH
        assert item.observed_value == 5

    def test_device_multi_account_reuse_medium_severity(self):
        """Verify 2 accounts on device produces MEDIUM severity DEVICE_MULTI_ACCOUNT_REUSE."""
        tx = {"device_account_count": 2}
        evidence = extract_structured_evidence(tx)
        assert len(evidence) == 1
        item = evidence[0]
        assert item.code == EvidenceSignalCode.DEVICE_MULTI_ACCOUNT_REUSE.value
        assert item.severity == EvidenceSeverity.MEDIUM
        assert item.observed_value == 2

    def test_unusual_location_signal(self):
        """Verify unusual location produces MEDIUM severity UNUSUAL_LOCATION."""
        tx = {"is_unusual_location": 1}
        evidence = extract_structured_evidence(tx)
        assert len(evidence) == 1
        item = evidence[0]
        assert item.code == EvidenceSignalCode.UNUSUAL_LOCATION.value
        assert item.severity == EvidenceSeverity.MEDIUM

    def test_unusual_time_signal(self):
        """Verify unusual time produces LOW severity UNUSUAL_TIME."""
        tx = {"is_unusual_time": 1}
        evidence = extract_structured_evidence(tx)
        assert len(evidence) == 1
        item = evidence[0]
        assert item.code == EvidenceSignalCode.UNUSUAL_TIME.value
        assert item.severity == EvidenceSeverity.LOW

    # -------------------------------------------------------------------------
    # 2. Multi-Signal, Severity Ordering, & Determinism
    # -------------------------------------------------------------------------
    def test_severity_ordering_and_all_signals_present(self):
        """Verify multiple simultaneous signals are ordered HIGH -> MEDIUM -> LOW."""
        tx = {
            "amount": 30000.0,
            "customer_avg_amount": 1000.0,  # HIGH (AMOUNT_SPIKE 30x)
            "transactions_last_10min": 4,   # HIGH (VELOCITY_BURST 4)
            "failed_attempts": 3,           # HIGH (FAILED_ATTEMPTS_BURST 3)
            "device_account_count": 4,      # HIGH (DEVICE_MULTI_ACCOUNT_REUSE 4)
            "is_new_device": 1,             # MEDIUM (NEW_DEVICE)
            "is_unusual_location": 1,       # MEDIUM (UNUSUAL_LOCATION)
            "is_unusual_time": 1,           # LOW (UNUSUAL_TIME)
        }
        evidence = extract_structured_evidence(tx)
        assert len(evidence) == 7

        # Verify strict non-ascending severity weights
        weights = [SEVERITY_WEIGHTS[e.severity] for e in evidence]
        assert weights == sorted(weights, reverse=True)

        # Verify all high severity items appear before medium, and medium before low
        severities = [e.severity for e in evidence]
        high_idx = [i for i, s in enumerate(severities) if s == EvidenceSeverity.HIGH]
        med_idx = [i for i, s in enumerate(severities) if s == EvidenceSeverity.MEDIUM]
        low_idx = [i for i, s in enumerate(severities) if s == EvidenceSeverity.LOW]

        assert max(high_idx) < min(med_idx)
        assert max(med_idx) < min(low_idx)

    def test_deterministic_evidence_sorting(self):
        """Verify repeat extractions yield 100% identical ordering and contents."""
        tx = {
            "amount": 15000.0,
            "customer_avg_amount": 2000.0,
            "transactions_last_10min": 2,
            "is_new_device": 1,
            "is_unusual_time": 1,
        }
        ref_evidence = extract_structured_evidence(tx)
        for _ in range(50):
            cur_evidence = extract_structured_evidence(tx)
            assert [e.model_dump() for e in cur_evidence] == [e.model_dump() for e in ref_evidence]

    def test_clean_transaction_empty_evidence(self):
        """Verify benign baseline transaction returns empty evidence list."""
        benign_tx = {
            "amount": 500.0,
            "customer_avg_amount": 500.0,
            "transactions_last_10min": 0,
            "transactions_last_1hr": 0,
            "failed_attempts": 0,
            "is_new_device": 0,
            "device_account_count": 1,
            "is_unusual_location": 0,
            "is_unusual_time": 0,
        }
        evidence = extract_structured_evidence(benign_tx)
        assert evidence == []

    # -------------------------------------------------------------------------
    # 3. Analyst Summary Generation
    # -------------------------------------------------------------------------
    def test_analyst_summary_for_clean_transaction(self):
        """Verify summary for clean transaction reflects baseline compliance."""
        summary = generate_analyst_summary([], "ALLOW", 10)
        assert "ALLOW" in summary
        assert "risk score 10" in summary
        assert "standard customer baselines" in summary

    def test_analyst_summary_for_high_risk_transaction(self):
        """Verify summary for high risk transaction includes signal counts and drivers."""
        tx = {
            "amount": 20000.0,
            "customer_avg_amount": 1000.0,
            "transactions_last_10min": 3,
            "failed_attempts": 2,
        }
        evidence = extract_structured_evidence(tx)
        summary = generate_analyst_summary(evidence, "BLOCK", 85)
        assert "BLOCK" in summary
        assert "risk score 85" in summary
        assert "Detected 3 risk signals" in summary
        assert "high-severity" in summary
