"""SQLite Database Initialization and Connection Management for RISK-X."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from app.core.config import settings

# Find project root directory
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent


def get_db_path() -> Path:
    """Resolve database path relative to project root or settings."""
    db_setting = Path(settings.DATABASE_PATH)
    if db_setting.is_absolute():
        db_path = db_setting
    else:
        # Check if project root/data exists or fallback
        db_path = ROOT_DIR / db_setting

    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def init_db(db_path: Path | None = None) -> None:
    """Initialize SQLite database tables and indexes."""
    target_path = db_path or get_db_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(target_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                customer_id TEXT,
                merchant_id TEXT,
                amount REAL NOT NULL,
                customer_avg_amount REAL NOT NULL DEFAULT 0.0,
                payment_method TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                fraud_probability REAL NOT NULL,
                decision TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                reasons_json TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                analyst_summary TEXT,
                raw_request_json TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'api',
                idempotency_key TEXT UNIQUE,
                created_at TEXT NOT NULL
            );
            """
        )

        # Performance and lookup indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_txn_id ON transactions (transaction_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions (created_at DESC);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_decision ON transactions (decision);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_risk_level ON transactions (risk_level);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_idempotency ON transactions (idempotency_key);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_customer_id ON transactions (customer_id);")

        conn.commit()


@contextmanager
def get_db(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for obtaining a database connection."""
    target_path = db_path or get_db_path()
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
