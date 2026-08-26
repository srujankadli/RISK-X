"""Transaction and Risk Assessment Repository."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from app.db.database import get_db, init_db


class TransactionRepository:
    """Repository handling persistence and queries for RISK-X transaction records."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path
        # Ensure schema exists
        init_db(self.db_path)

    def save_transaction(
        self,
        transaction_id: str,
        amount: float,
        customer_avg_amount: float,
        payment_method: str,
        risk_score: int,
        fraud_probability: float,
        decision: str,
        risk_level: str,
        reasons: List[str],
        evidence: List[Dict[str, Any]],
        raw_request: Dict[str, Any],
        customer_id: Optional[str] = None,
        merchant_id: Optional[str] = None,
        analyst_summary: Optional[str] = None,
        source: str = "api",
        idempotency_key: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save a new transaction assessment record to the database."""
        timestamp = created_at or datetime.now(timezone.utc).isoformat()
        reasons_json = json.dumps(reasons)
        evidence_json = json.dumps(evidence)
        raw_request_json = json.dumps(raw_request)

        try:
            with get_db(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO transactions (
                        transaction_id,
                        customer_id,
                        merchant_id,
                        amount,
                        customer_avg_amount,
                        payment_method,
                        risk_score,
                        fraud_probability,
                        decision,
                        risk_level,
                        reasons_json,
                        evidence_json,
                        analyst_summary,
                        raw_request_json,
                        source,
                        idempotency_key,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        transaction_id,
                        customer_id,
                        merchant_id,
                        amount,
                        customer_avg_amount,
                        payment_method,
                        risk_score,
                        fraud_probability,
                        decision,
                        risk_level,
                        reasons_json,
                        evidence_json,
                        analyst_summary,
                        raw_request_json,
                        source,
                        idempotency_key,
                        timestamp,
                    ),
                )
                conn.commit()
        except Exception:
            # Handle concurrent duplicate inserts gracefully
            if idempotency_key:
                existing = self.get_transaction_by_idempotency_key(idempotency_key)
                if existing:
                    return existing
            existing_by_id = self.get_transaction_by_id(transaction_id)
            if existing_by_id:
                return existing_by_id
            raise

        return self.get_transaction_by_id(transaction_id) or {}

    def get_transaction_by_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a transaction record by its unique transaction_id."""
        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM transactions WHERE transaction_id = ? LIMIT 1;",
                (transaction_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_dict(row)

    def get_transaction_by_idempotency_key(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a transaction record by its idempotency key."""
        if not idempotency_key:
            return None
        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM transactions WHERE idempotency_key = ? LIMIT 1;",
                (idempotency_key,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_dict(row)

    def list_transactions(
        self,
        limit: int = 50,
        offset: int = 0,
        decision: Optional[str] = None,
        risk_level: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List transactions with optional filters and pagination."""
        query_clauses = []
        params: List[Any] = []

        if decision:
            query_clauses.append("decision = ?")
            params.append(decision.upper())

        if risk_level:
            query_clauses.append("risk_level = ?")
            params.append(risk_level.upper())

        if search:
            query_clauses.append("(transaction_id LIKE ? OR customer_id LIKE ? OR merchant_id LIKE ?)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])

        where_str = f"WHERE {' AND '.join(query_clauses)}" if query_clauses else ""

        with get_db(self.db_path) as conn:
            cursor = conn.cursor()

            # Count total matching
            count_query = f"SELECT COUNT(*) FROM transactions {where_str};"
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            # Fetch paginated rows
            select_query = f"""
                SELECT * FROM transactions
                {where_str}
                ORDER BY created_at DESC, id DESC
                LIMIT ? OFFSET ?;
            """
            cursor.execute(select_query, params + [limit, offset])
            rows = cursor.fetchall()
            items = [self._row_to_dict(r) for r in rows]

        return items, total

    def get_risk_stats(self) -> Dict[str, Any]:
        """Compute aggregate risk assessment metrics for dashboard overview."""
        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN decision = 'ALLOW' THEN 1 ELSE 0 END) AS allow_count,
                    SUM(CASE WHEN decision = 'REVIEW' THEN 1 ELSE 0 END) AS review_count,
                    SUM(CASE WHEN decision = 'BLOCK' THEN 1 ELSE 0 END) AS block_count,
                    AVG(risk_score) AS avg_score,
                    AVG(fraud_probability) AS avg_prob
                FROM transactions;
                """
            )
            row = cursor.fetchone()
            total = row["total"] or 0
            allow_count = row["allow_count"] or 0
            review_count = row["review_count"] or 0
            block_count = row["block_count"] or 0
            avg_score = round(float(row["avg_score"] or 0.0), 1)
            avg_prob = round(float(row["avg_prob"] or 0.0), 4)

            return {
                "total_transactions": total,
                "allow_count": allow_count,
                "review_count": review_count,
                "block_count": block_count,
                "allow_rate": round((allow_count / total * 100) if total > 0 else 0.0, 1),
                "review_rate": round((review_count / total * 100) if total > 0 else 0.0, 1),
                "block_rate": round((block_count / total * 100) if total > 0 else 0.0, 1),
                "average_risk_score": avg_score,
                "average_fraud_probability": avg_prob,
            }

    @staticmethod
    def _row_to_dict(row: Any) -> Dict[str, Any]:
        """Convert a sqlite3.Row to a clean Python dictionary."""
        d = dict(row)
        # Parse JSON fields safely
        try:
            d["reasons"] = json.loads(d.get("reasons_json") or "[]")
        except Exception:
            d["reasons"] = []
        try:
            d["evidence"] = json.loads(d.get("evidence_json") or "[]")
        except Exception:
            d["evidence"] = []
        try:
            d["raw_request"] = json.loads(d.get("raw_request_json") or "{}")
        except Exception:
            d["raw_request"] = {}

        # Remove redundant JSON string columns
        d.pop("reasons_json", None)
        d.pop("evidence_json", None)
        d.pop("raw_request_json", None)
        return d


_repository_instance: Optional[TransactionRepository] = None


def get_transaction_repository() -> TransactionRepository:
    """Singleton getter for the transaction repository."""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = TransactionRepository()
    return _repository_instance
