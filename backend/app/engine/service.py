"""
RISK-X Risk Assessment Service
==============================
Coordinates feature extraction, ML inference, deterministic risk scoring,
policy decisioning, structured evidence extraction, and analyst explanation generation.
"""

from enum import Enum
import os
from pathlib import Path
import sys
from typing import Any, Dict, Optional, Union
import joblib
import pandas as pd

# Resolve project root and ensure it is on sys.path for `ml` package deserialization
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.engine.scoring import calculate_risk_score
from app.engine.decision import evaluate_decision, Decision, RiskLevel
from app.engine.reasons import extract_risk_reasons
from app.engine.evidence import extract_structured_evidence, generate_analyst_summary
from app.schemas.risk import (
    TransactionAssessmentRequest,
    RiskAssessmentResponse,
    DecisionEnum,
    RiskLevelEnum,
    EvidenceItem as SchemaEvidenceItem,
    EvidenceSeverityEnum,
)

DEFAULT_MODEL_PATH = ROOT_DIR / "ml" / "models" / "random_forest_detector.joblib"
DEFAULT_PREPROCESSOR_PATH = ROOT_DIR / "ml" / "models" / "preprocessor.joblib"


class RiskEngineService:
    """Service for executing real-time risk assessments with in-memory cached models and rules."""

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        preprocessor_path: Optional[Union[str, Path]] = None,
    ):
        self.model_path = Path(model_path or DEFAULT_MODEL_PATH)
        self.preprocessor_path = Path(preprocessor_path or DEFAULT_PREPROCESSOR_PATH)
        self._model = None
        self._preprocessor = None

    def _ensure_artifacts_loaded(self):
        """
        Loads serialized model and preprocessor artifacts into memory once on first demand.
        Subsequent requests reuse the loaded in-memory objects (zero disk I/O per request).
        """
        if self._model is None or self._preprocessor is None:
            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"Model artifact not found at {self.model_path}. Please run `python ml/train_model.py`."
                )
            if not self.preprocessor_path.exists():
                raise FileNotFoundError(
                    f"Preprocessor artifact not found at {self.preprocessor_path}. Please run `python ml/train_model.py`."
                )
            try:
                self._preprocessor = joblib.load(self.preprocessor_path)
                self._model = joblib.load(self.model_path)
            except Exception as e:
                self._preprocessor = None
                self._model = None
                raise RuntimeError(f"Failed to deserialize ML model artifacts: {str(e)}") from e

    def check_readiness(self) -> Dict[str, Any]:
        """
        Checks whether model and preprocessor artifacts are accessible and loadable.
        Returns readiness status details without throwing unhandled exceptions.
        """
        try:
            self._ensure_artifacts_loaded()
            return {
                "ready": True,
                "status": "ready",
                "model_loaded": True,
                "preprocessor_loaded": True,
                "model_path": str(self.model_path),
                "preprocessor_path": str(self.preprocessor_path),
            }
        except Exception as e:
            return {
                "ready": False,
                "status": "unready",
                "model_loaded": self._model is not None,
                "preprocessor_loaded": self._preprocessor is not None,
                "error": str(e),
            }

    def assess_transaction(
        self,
        transaction: Union[TransactionAssessmentRequest, Dict[str, Any]],
        persist: bool = True,
        source: str = "api",
        idempotency_key: Optional[str] = None,
    ) -> RiskAssessmentResponse:
        """
        Executes end-to-end risk assessment for an incoming transaction:
        1. Validates and extracts observable transaction features
        2. Transforms features through preprocessor ColumnTransformer
        3. Computes fraud probability via Random Forest detector
        4. Maps probability to deterministic 0-100 risk score
        5. Evaluates ALLOW / REVIEW / BLOCK decision policy
        6. Extracts explainable risk reasons & structured evidence items
        7. Synthesizes concise analyst-facing narrative summary
        8. Persists assessment result to transaction ledger

        Args:
            transaction: Transaction data payload (Request schema or dictionary).
            persist: If True, persists the transaction record to SQLite ledger.
            source: Ingestion source channel ('api', 'webhook', etc.).
            idempotency_key: Optional deduplication key.

        Returns:
            RiskAssessmentResponse with score, decision, risk level, reasons, evidence, and analyst summary.
        """
        self._ensure_artifacts_loaded()

        if isinstance(transaction, TransactionAssessmentRequest):
            raw_dict = transaction.model_dump()
            # Convert enum to raw string for preprocessor if needed
            if isinstance(raw_dict.get("payment_method"), Enum):
                raw_dict["payment_method"] = raw_dict["payment_method"].value
        else:
            raw_dict = dict(transaction)

        # Convert to single-row DataFrame for preprocessor ColumnTransformer
        df_row = pd.DataFrame([raw_dict])

        # Step 1 & 2: Feature pipeline transformation and model inference
        X_proc = self._preprocessor.transform(df_row)
        fraud_prob = float(self._model.predict_proba(X_proc)[0, 1])

        # Step 3: Deterministic risk score calculation
        risk_score = calculate_risk_score(fraud_prob)

        # Step 4: Decision policy evaluation
        decision, risk_level = evaluate_decision(risk_score)

        # Step 5: Explainable risk reason extraction (backward-compatible strings)
        reasons = extract_risk_reasons(raw_dict)

        # Step 6: Structured evidence extraction and ranking
        evidence_items = extract_structured_evidence(raw_dict)

        # Map to schema EvidenceItem models
        schema_evidence = [
            SchemaEvidenceItem(
                code=e.code,
                severity=EvidenceSeverityEnum(e.severity.value),
                title=e.title,
                description=e.description,
                observed_value=e.observed_value,
                reference_threshold=e.reference_threshold,
            )
            for e in evidence_items
        ]

        # Step 7: Analyst explanation summary
        analyst_summary = generate_analyst_summary(evidence_items, decision.value, risk_score)

        txn_id = raw_dict.get("transaction_id")

        # Step 8: Optional persistence to SQLite transaction repository
        if persist:
            try:
                import uuid
                from app.db.repository import get_transaction_repository
                repo = get_transaction_repository()
                effective_id = txn_id or f"txn_{uuid.uuid4().hex[:12]}"
                repo.save_transaction(
                    transaction_id=effective_id,
                    amount=float(raw_dict.get("amount", 0.0)),
                    customer_avg_amount=float(raw_dict.get("customer_avg_amount", 0.0)),
                    payment_method=str(raw_dict.get("payment_method", "card")),
                    risk_score=risk_score,
                    fraud_probability=round(fraud_prob, 4),
                    decision=decision.value,
                    risk_level=risk_level.value,
                    reasons=reasons,
                    evidence=[e.model_dump() for e in schema_evidence],
                    raw_request=raw_dict,
                    customer_id=raw_dict.get("customer_id"),
                    merchant_id=raw_dict.get("merchant_id"),
                    analyst_summary=analyst_summary,
                    source=source,
                    idempotency_key=idempotency_key,
                )
                if not txn_id:
                    txn_id = effective_id
            except Exception:
                # Ensure inference continues even if optional DB logging encounters an issue
                pass

        return RiskAssessmentResponse(
            risk_score=risk_score,
            fraud_probability=round(fraud_prob, 4),
            decision=DecisionEnum(decision.value),
            risk_level=RiskLevelEnum(risk_level.value),
            reasons=reasons,
            evidence=schema_evidence,
            analyst_summary=analyst_summary,
            transaction_id=txn_id,
        )


# Global default service instance
risk_service = RiskEngineService()
