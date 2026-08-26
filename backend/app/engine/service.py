"""
RISK-X Risk Assessment Service
==============================
Coordinates feature extraction, ML inference, deterministic risk scoring,
policy decisioning, and explainable reason generation.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
import joblib
import pandas as pd

from app.engine.scoring import calculate_risk_score
from app.engine.decision import evaluate_decision, Decision, RiskLevel
from app.engine.reasons import extract_risk_reasons
from app.schemas.risk import (
    TransactionAssessmentRequest,
    RiskAssessmentResponse,
    DecisionEnum,
    RiskLevelEnum,
)

# Resolve default model artifact paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_MODEL_PATH = ROOT_DIR / "ml" / "models" / "random_forest_detector.joblib"
DEFAULT_PREPROCESSOR_PATH = ROOT_DIR / "ml" / "models" / "preprocessor.joblib"


class RiskEngineService:
    """Singleton/Service for executing risk assessments with loaded models and rules."""

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
        """Loads serialized model artifacts on first demand."""
        if self._model is None or self._preprocessor is None:
            if not self.model_path.exists() or not self.preprocessor_path.exists():
                raise FileNotFoundError(
                    f"Model artifacts not found at {self.model_path} or {self.preprocessor_path}. "
                    "Please run `python ml/train_model.py` first."
                )
            self._preprocessor = joblib.load(self.preprocessor_path)
            self._model = joblib.load(self.model_path)

    def assess_transaction(
        self, transaction: Union[TransactionAssessmentRequest, Dict[str, Any]]
    ) -> RiskAssessmentResponse:
        """
        Executes end-to-end risk assessment for an incoming transaction:
        1. Transforms transaction through feature pipeline
        2. Computes fraud probability via Random Forest detector
        3. Maps probability to deterministic 0-100 risk score
        4. Evaluates ALLOW / REVIEW / BLOCK decision policy
        5. Extracts explainable risk reasons

        Args:
            transaction: Transaction data payload (Request schema or dictionary).

        Returns:
            RiskAssessmentResponse with score, decision, risk level, and reasons.
        """
        self._ensure_artifacts_loaded()

        if isinstance(transaction, TransactionAssessmentRequest):
            raw_dict = transaction.model_dump()
        else:
            raw_dict = dict(transaction)

        # Convert to single-row DataFrame for preprocessor
        df_row = pd.DataFrame([raw_dict])

        # Step 1 & 2: Feature pipeline transformation and model inference
        X_proc = self._preprocessor.transform(df_row)
        fraud_prob = float(self._model.predict_proba(X_proc)[0, 1])

        # Step 3: Deterministic risk score calculation
        risk_score = calculate_risk_score(fraud_prob)

        # Step 4: Decision policy evaluation
        decision, risk_level = evaluate_decision(risk_score)

        # Step 5: Explainable risk reason extraction
        reasons = extract_risk_reasons(raw_dict)

        return RiskAssessmentResponse(
            risk_score=risk_score,
            fraud_probability=round(fraud_prob, 4),
            decision=DecisionEnum(decision.value),
            risk_level=RiskLevelEnum(risk_level.value),
            reasons=reasons,
            transaction_id=raw_dict.get("transaction_id"),
        )


# Global default service instance
risk_service = RiskEngineService()
