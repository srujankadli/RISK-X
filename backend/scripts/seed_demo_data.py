"""
RISK-X Demo Database Seeder and Reset Utility
=============================================
Provides a safe, reproducible mechanism to reset or populate the local SQLite ledger
with curated, realistic demo transactions evaluated via the real RiskEngineService ML pipeline.

Usage:
    # Reset and seed professional demo transactions (default):
    python backend/scripts/seed_demo_data.py

    # Reset to a clean, empty database:
    python backend/scripts/seed_demo_data.py --clean

    # Seed without dropping existing data:
    python backend/scripts/seed_demo_data.py --append
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure root and backend directories are in Python path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

for p in [str(ROOT_DIR), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.core.config import settings
from app.db.database import get_db, init_db
from app.db.repository import get_transaction_repository
from app.engine.service import risk_service

DEMO_TRANSACTIONS = [
    {
        "transaction_id": "txn_demo_001",
        "customer_id": "cust_ind_1048",
        "merchant_id": "mer_retail_01",
        "amount": 450.0,
        "customer_avg_amount": 500.0,
        "payment_method": "upi",
        "account_age_days": 320,
        "previous_transaction_count": 42,
        "failed_attempts": 0,
        "refund_count": 0,
        "transactions_last_10min": 0,
        "transactions_last_1hr": 0,
        "device_account_count": 1,
        "is_new_device": 0,
        "is_unusual_time": 0,
        "is_unusual_location": 0,
        "source": "api",
        "time_offset_minutes": -45,
    },
    {
        "transaction_id": "txn_demo_002",
        "customer_id": "cust_ind_2931",
        "merchant_id": "mer_ecommerce_04",
        "amount": 1250.0,
        "customer_avg_amount": 1200.0,
        "payment_method": "card",
        "account_age_days": 180,
        "previous_transaction_count": 25,
        "failed_attempts": 0,
        "refund_count": 0,
        "transactions_last_10min": 0,
        "transactions_last_1hr": 0,
        "device_account_count": 1,
        "is_new_device": 0,
        "is_unusual_time": 0,
        "is_unusual_location": 0,
        "source": "api",
        "time_offset_minutes": -35,
    },
    {
        "transaction_id": "txn_demo_003",
        "customer_id": "cust_biz_8820",
        "merchant_id": "mer_b2b_saas_02",
        "amount": 3800.0,
        "customer_avg_amount": 4000.0,
        "payment_method": "netbanking",
        "account_age_days": 450,
        "previous_transaction_count": 88,
        "failed_attempts": 0,
        "refund_count": 0,
        "transactions_last_10min": 0,
        "transactions_last_1hr": 0,
        "device_account_count": 1,
        "is_new_device": 0,
        "is_unusual_time": 0,
        "is_unusual_location": 0,
        "source": "api",
        "time_offset_minutes": -25,
    },
    {
        "transaction_id": "txn_demo_004",
        "customer_id": "cust_biz_3910",
        "merchant_id": "mer_travel_09",
        "amount": 2800.0,
        "customer_avg_amount": 1000.0,
        "payment_method": "card",
        "account_age_days": 100,
        "previous_transaction_count": 12,
        "failed_attempts": 1,
        "refund_count": 0,
        "transactions_last_10min": 0,
        "transactions_last_1hr": 1,
        "device_account_count": 1,
        "is_new_device": 1,
        "is_unusual_time": 1,
        "is_unusual_location": 0,
        "source": "api",
        "time_offset_minutes": -15,
    },
    {
        "transaction_id": "pay_demo_7821",
        "customer_id": "cust_hook_sim_89",
        "merchant_id": "mer_fashion_12",
        "amount": 3500.0,
        "customer_avg_amount": 1400.0,
        "payment_method": "card",
        "account_age_days": 60,
        "previous_transaction_count": 5,
        "failed_attempts": 1,
        "refund_count": 0,
        "transactions_last_10min": 0,
        "transactions_last_1hr": 1,
        "device_account_count": 1,
        "is_new_device": 1,
        "is_unusual_time": 1,
        "is_unusual_location": 0,
        "source": "webhook",
        "idempotency_key": "pay_demo_7821",
        "time_offset_minutes": -8,
    },
    {
        "transaction_id": "txn_demo_005",
        "customer_id": "cust_ind_8402",
        "merchant_id": "mer_crypto_fin_05",
        "amount": 55000.0,
        "customer_avg_amount": 1000.0,
        "payment_method": "card",
        "account_age_days": 8,
        "previous_transaction_count": 0,
        "failed_attempts": 3,
        "refund_count": 0,
        "transactions_last_10min": 3,
        "transactions_last_1hr": 5,
        "device_account_count": 4,
        "is_new_device": 1,
        "is_unusual_time": 1,
        "is_unusual_location": 1,
        "source": "api",
        "time_offset_minutes": -2,
    },
]


def reset_database(db_path: Path = None) -> None:
    """Wipes and recreates the SQLite transactions table."""
    target_path = db_path or Path(settings.DATABASE_PATH)
    if target_path.exists():
        target_path.unlink()
    init_db(target_path)
    print(f"[*] Reset SQLite database schema at: {target_path}")


def seed_demo_data(db_path: Path = None) -> None:
    """Evaluates and seeds realistic demo transactions via the real ML RiskEngineService."""
    repo = get_transaction_repository()
    now = datetime.now(timezone.utc)

    print(f"[*] Evaluating and seeding {len(DEMO_TRANSACTIONS)} curated demo transactions...")
    print("-" * 75)

    for spec in DEMO_TRANSACTIONS:
        txn_data = dict(spec)
        offset = txn_data.pop("time_offset_minutes", 0)
        source = txn_data.get("source", "api")
        idempotency_key = txn_data.get("idempotency_key")
        created_at = (now + timedelta(minutes=offset)).isoformat()

        # Assess via real model (without automatic save so we can set created_at timestamp)
        assessment = risk_service.assess_transaction(txn_data, persist=False)

        # Save with calculated scores and formatted timestamp
        repo.save_transaction(
            transaction_id=txn_data["transaction_id"],
            amount=txn_data["amount"],
            customer_avg_amount=txn_data.get("customer_avg_amount", 0.0),
            payment_method=txn_data.get("payment_method", "card"),
            risk_score=assessment.risk_score,
            fraud_probability=assessment.fraud_probability,
            decision=assessment.decision.value,
            risk_level=assessment.risk_level.value,
            reasons=assessment.reasons,
            evidence=[e.model_dump() for e in assessment.evidence],
            raw_request=txn_data,
            customer_id=txn_data.get("customer_id"),
            merchant_id=txn_data.get("merchant_id"),
            analyst_summary=assessment.analyst_summary,
            source=source,
            idempotency_key=idempotency_key,
            created_at=created_at,
        )

        print(
            f"  {txn_data['transaction_id']:<18} | INR {txn_data['amount']:>8.2f} | "
            f"Score: {assessment.risk_score:>2} | Decision: {assessment.decision.value:<6} | "
            f"Source: {source:<7} | Signals: {len(assessment.evidence)}"
        )

    print("-" * 75)
    stats = repo.get_risk_stats()
    print(
        f"[+] Seed Complete! Total: {stats['total_transactions']} | "
        f"ALLOW: {stats['allow_count']} ({stats['allow_rate']}%) | "
        f"REVIEW: {stats['review_count']} ({stats['review_rate']}%) | "
        f"BLOCK: {stats['block_count']} ({stats['block_rate']}%) | "
        f"Avg Score: {stats['average_risk_score']}"
    )


def main():
    parser = argparse.ArgumentParser(description="RISK-X Demo Database Management Utility")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Wipe the database and initialize a clean empty schema without seeding.",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Seed demo transactions without dropping existing database records.",
    )
    args = parser.parse_args()

    if args.clean:
        reset_database()
        print("[+] Clean database initialization finished.")
    elif args.append:
        seed_demo_data()
    else:
        # Default: fresh reset + seed
        reset_database()
        seed_demo_data()


if __name__ == "__main__":
    main()
