"""Unit tests for SQLite database layer and TransactionRepository."""

import tempfile
from pathlib import Path
import pytest
from app.db.database import init_db
from app.db.repository import TransactionRepository


@pytest.fixture
def temp_repo(tmp_path: Path) -> TransactionRepository:
    """Fixture providing an isolated TransactionRepository using a temporary database."""
    db_file = tmp_path / "test_risk_x.db"
    return TransactionRepository(db_path=db_file)


class TestDatabaseAndRepository:
    """Test suite for SQLite transaction persistence and queries."""

    def test_database_initialization(self, tmp_path: Path):
        db_file = tmp_path / "test_init.db"
        init_db(db_file)
        assert db_file.exists()

    def test_save_and_retrieve_transaction(self, temp_repo: TransactionRepository):
        tx = temp_repo.save_transaction(
            transaction_id="txn_test_101",
            customer_id="cust_001",
            merchant_id="mer_001",
            amount=1500.0,
            customer_avg_amount=1000.0,
            payment_method="card",
            risk_score=65,
            fraud_probability=0.6482,
            decision="REVIEW",
            risk_level="MEDIUM",
            reasons=["Risk signal: previous failed payment attempt."],
            evidence=[{"code": "FAILED_ATTEMPT_PRIOR", "severity": "LOW"}],
            raw_request={"amount": 1500.0},
            analyst_summary="Review recommended due to prior failure.",
            source="api",
            idempotency_key="idemp_101",
        )

        assert tx["transaction_id"] == "txn_test_101"
        assert tx["amount"] == 1500.0
        assert tx["risk_score"] == 65
        assert tx["decision"] == "REVIEW"
        assert tx["reasons"] == ["Risk signal: previous failed payment attempt."]
        assert len(tx["evidence"]) == 1

        # Retrieve by ID
        retrieved = temp_repo.get_transaction_by_id("txn_test_101")
        assert retrieved is not None
        assert retrieved["transaction_id"] == "txn_test_101"
        assert retrieved["customer_id"] == "cust_001"
        assert retrieved["idempotency_key"] == "idemp_101"

    def test_get_transaction_by_idempotency_key(self, temp_repo: TransactionRepository):
        temp_repo.save_transaction(
            transaction_id="txn_idemp_1",
            amount=500.0,
            customer_avg_amount=500.0,
            payment_method="upi",
            risk_score=10,
            fraud_probability=0.1,
            decision="ALLOW",
            risk_level="LOW",
            reasons=[],
            evidence=[],
            raw_request={},
            idempotency_key="pay_unique_key_999",
        )

        found = temp_repo.get_transaction_by_idempotency_key("pay_unique_key_999")
        assert found is not None
        assert found["transaction_id"] == "txn_idemp_1"

        not_found = temp_repo.get_transaction_by_idempotency_key("non_existent_key")
        assert not_found is None

    def test_list_transactions_filtering_and_pagination(self, temp_repo: TransactionRepository):
        # Insert 3 transactions with different decisions
        temp_repo.save_transaction(
            transaction_id="txn_allow_1",
            amount=200.0,
            customer_avg_amount=200.0,
            payment_method="upi",
            risk_score=5,
            fraud_probability=0.05,
            decision="ALLOW",
            risk_level="LOW",
            reasons=[],
            evidence=[],
            raw_request={},
            customer_id="cust_alpha",
        )
        temp_repo.save_transaction(
            transaction_id="txn_review_1",
            amount=3000.0,
            customer_avg_amount=1000.0,
            payment_method="card",
            risk_score=55,
            fraud_probability=0.55,
            decision="REVIEW",
            risk_level="MEDIUM",
            reasons=[],
            evidence=[],
            raw_request={},
            customer_id="cust_beta",
        )
        temp_repo.save_transaction(
            transaction_id="txn_block_1",
            amount=50000.0,
            customer_avg_amount=1000.0,
            payment_method="card",
            risk_score=90,
            fraud_probability=0.90,
            decision="BLOCK",
            risk_level="HIGH",
            reasons=[],
            evidence=[],
            raw_request={},
            customer_id="cust_gamma",
        )

        # List all
        items, total = temp_repo.list_transactions(limit=10, offset=0)
        assert total == 3
        assert len(items) == 3

        # Filter by decision ALLOW
        allow_items, allow_total = temp_repo.list_transactions(decision="ALLOW")
        assert allow_total == 1
        assert allow_items[0]["transaction_id"] == "txn_allow_1"

        # Filter by decision BLOCK
        block_items, block_total = temp_repo.list_transactions(decision="BLOCK")
        assert block_total == 1
        assert block_items[0]["transaction_id"] == "txn_block_1"

        # Search by customer ID
        searched, s_total = temp_repo.list_transactions(search="beta")
        assert s_total == 1
        assert searched[0]["transaction_id"] == "txn_review_1"

        # Pagination limit
        p_items, p_total = temp_repo.list_transactions(limit=2, offset=0)
        assert p_total == 3
        assert len(p_items) == 2

    def test_get_risk_stats(self, temp_repo: TransactionRepository):
        temp_repo.save_transaction(
            transaction_id="txn_s1",
            amount=100.0,
            customer_avg_amount=100.0,
            payment_method="upi",
            risk_score=10,
            fraud_probability=0.1,
            decision="ALLOW",
            risk_level="LOW",
            reasons=[],
            evidence=[],
            raw_request={},
        )
        temp_repo.save_transaction(
            transaction_id="txn_s2",
            amount=5000.0,
            customer_avg_amount=1000.0,
            payment_method="card",
            risk_score=90,
            fraud_probability=0.9,
            decision="BLOCK",
            risk_level="HIGH",
            reasons=[],
            evidence=[],
            raw_request={},
        )

        stats = temp_repo.get_risk_stats()
        assert stats["total_transactions"] == 2
        assert stats["allow_count"] == 1
        assert stats["block_count"] == 1
        assert stats["review_count"] == 0
        assert stats["allow_rate"] == 50.0
        assert stats["block_rate"] == 50.0
        assert stats["average_risk_score"] == 50.0

    def test_empty_database_stats_and_listing(self, temp_repo: TransactionRepository):
        """Verify empty database returns clean zeroed statistics and empty list."""
        stats = temp_repo.get_risk_stats()
        assert stats["total_transactions"] == 0
        assert stats["allow_count"] == 0
        assert stats["review_count"] == 0
        assert stats["block_count"] == 0
        assert stats["allow_rate"] == 0.0
        assert stats["average_risk_score"] == 0.0

        items, total = temp_repo.list_transactions()
        assert items == []
        assert total == 0

    def test_concurrent_duplicate_idempotency_insert_returns_existing(self, temp_repo: TransactionRepository):
        """Verify duplicate insert with identical idempotency key returns existing record without throwing error."""
        t1 = temp_repo.save_transaction(
            transaction_id="txn_dup_1",
            amount=1000.0,
            customer_avg_amount=1000.0,
            payment_method="card",
            risk_score=20,
            fraud_probability=0.2,
            decision="ALLOW",
            risk_level="LOW",
            reasons=[],
            evidence=[],
            raw_request={"amount": 1000.0},
            idempotency_key="idemp_dup_999",
        )

        # Second insert with same idempotency key
        t2 = temp_repo.save_transaction(
            transaction_id="txn_dup_2_attempted",
            amount=2000.0,
            customer_avg_amount=1000.0,
            payment_method="card",
            risk_score=80,
            fraud_probability=0.8,
            decision="BLOCK",
            risk_level="HIGH",
            reasons=[],
            evidence=[],
            raw_request={"amount": 2000.0},
            idempotency_key="idemp_dup_999",
        )

        # Returns original existing record
        assert t2["transaction_id"] == "txn_dup_1"
        assert t2["risk_score"] == 20
        assert t2["decision"] == "ALLOW"
