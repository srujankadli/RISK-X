# RISK-X Machine Learning Engine

This directory houses the machine learning models, feature engineering pipelines, and evaluation routines for payment fraud detection.

---

## Structure

```
ml/
├── models/             # Serialized model artifacts (.joblib / .pkl)
├── pipelines/          # Feature transformers, scalers, encoders
└── README.md
```

---

## Strategy (Incremental)

1. **Feature Engineering**:
   - Velocity features (transactions per card/user in 1h, 24h, 7d).
   - Deviation features (amount vs. user historical mean).
   - Device and geographic risk signals (IP mismatch, proxy detection, country risk).
2. **Model Selection**:
   - Baseline: `scikit-learn` IsolationForest / RandomForest / LogisticRegression for transparent, interpretable scoring.
   - Supervised classification calibrated with probability outputs for the 0-100 risk score.
3. **Inference**:
   - Lightweight model artifact loaded into the FastAPI runtime for sub-millisecond evaluation.
