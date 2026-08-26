# RISK-X Machine Learning Risk Detector

Production-quality ML detection layer for payment risk analysis in RISK-X.

---

## 1. Directory Structure

```
ml/
├── models/
│   ├── preprocessor.joblib              # Fitted feature engineering & scaling pipeline
│   ├── logistic_regression_baseline.joblib # Trained baseline classifier
│   ├── random_forest_detector.joblib    # Trained Random Forest classifier
│   ├── training_summary.json            # Validation metrics & threshold grid
│   └── evaluation_metrics.json          # Held-out test results & cost modeling
├── pipelines/
│   ├── __init__.py
│   └── feature_pipeline.py              # Scikit-learn ColumnTransformer & FeatureEngineer
├── train_model.py                       # Chronological training & threshold selection CLI
├── evaluate_model.py                     # Held-out test evaluation & cost analysis CLI
├── __init__.py
└── README.md
```

---

## 2. Temporal Chronological Splitting

To prevent lookahead data leakage in time-series transaction streams, data is split strictly chronologically by `timestamp`:
- **TRAIN (70%)**: Earliest 35,000 transactions (`2026-06-01T06:01:01Z` to `2026-06-14T04:13:06Z`) — Suspicious rate: **8.17%**
- **VALIDATION (15%)**: Next 7,500 transactions (`2026-06-14T04:16:56Z` to `2026-06-16T21:19:24Z`) — Suspicious rate: **6.60%**
- **HELD-OUT TEST (15%)**: Latest 7,500 transactions (`2026-06-16T21:19:48Z` to `2026-06-19T15:55:29Z`) — Suspicious rate: **5.27%**

> **Leakage Prevention**: Preprocessor is fitted on **TRAIN ONLY**. Validation set is used for model comparison, validation-cost analysis, and threshold tuning. The **HELD-OUT TEST SET** remains completely untouched until final evaluation.

---

## 3. Feature Engineering

Features are constructed exclusively from observable state available at transaction time $t$:

### Observable Features
- `amount`: Transaction amount (INR)
- `account_age_days`: Account age in days
- `previous_transaction_count`: Historical transaction count
- `failed_attempts`: Immediate failed attempts
- `refund_count`: Historical refund count
- `customer_avg_amount`: Historical customer average amount
- `transactions_last_10min`: Rolling count in $[t - 10\text{min}, t)$
- `transactions_last_1hr`: Rolling count in $[t - 1\text{hr}, t)$
- `device_account_count`: Unique accounts observed on device up to $t$
- `is_new_device`: Binary indicator
- `is_unusual_time`: Binary indicator
- `is_unusual_location`: Binary indicator
- `payment_method`: One-hot encoded (`card`, `netbanking`, `upi`, `wallet`)

### Derived Behavioral Features
1. `amount_to_customer_avg_ratio` = $\frac{\text{amount}}{\text{customer\_avg\_amount} + 10^{-5}}$
2. `log_amount` = $\ln(1 + \text{amount})$
3. `velocity_ratio` = $\frac{\text{transactions\_last\_10min}}{\text{transactions\_last\_1hr} + 1.0}$
4. `device_reuse_ratio` = $\frac{\text{device\_account\_count}}{\text{previous\_transaction\_count} + 1.0}$

---

## 4. Model Comparison (Validation Set)

Evaluated on the 7,500 validation transactions at default 0.50 threshold:

| Metric | Baseline (Logistic Regression) | Stronger Model (Random Forest) |
|---|---|---|
| **Precision** | 0.6204 (62.04%) | **0.7464 (74.64%)** |
| **Recall** | 0.8848 (88.48%) | **0.9394 (93.94%)** |
| **F1-Score** | 0.7294 | **0.8318** |
| **ROC-AUC** | 0.9791 | **0.9942** |
| **PR-AUC** | 0.8820 | **0.9532** |
| **FPR** | 0.0383 (3.83%) | **0.0226 (2.26%)** |

---

## 5. Threshold Selection (Validation Set Operating Grid)

Evaluated across operating thresholds strictly on the **Validation set** for Random Forest:

| Threshold | Precision | Recall | F1-Score | FPR | True Positives | False Positives | False Negatives | Sim. Cost (INR)* |
|---|---|---|---|---|---|---|---|---|
| 0.30 | 0.3670 | 0.9919 | 0.5357 | 0.1209 | 491 | 847 | 4 | INR 221,750 |
| 0.40 | 0.4350 | 0.9737 | 0.6014 | 0.0894 | 482 | 626 | 13 | INR 189,000 |
| 0.50 | 0.7464 | 0.9394 | 0.8318 | 0.0226 | 465 | 158 | 30 | INR 114,500 |
| **0.60 (Selected)** | **0.8911** | **0.9091** | **0.9000** | **0.0079** | **450** | **55** | **45** | **INR 126,250** |
| 0.70 | 0.9502 | 0.8869 | 0.9175 | 0.0033 | 439 | 23 | 56 | INR 145,750 |
| 0.80 | 0.9596 | 0.8646 | 0.9097 | 0.0026 | 428 | 18 | 67 | INR 172,000 |

*\*Simulation assumptions: Unit FP Cost = INR 250, Unit FN Cost = INR 2,500 (not actual Razorpay costs).*

### Selection Justification:
> **Threshold 0.60 is an operational operating point chosen to balance high suspicious-event recall (>90% on validation) with high precision (89.11%) and a sub-1% false-positive rate (0.79%). Threshold 0.70 has a higher validation F1, but 0.60 retains higher recall.**
> *The simulated cost model is illustrative and was not used as the threshold-selection objective.*

---

## 6. Final Held-Out Test Results (Single Evaluation Pass)

Evaluated exactly once on the **7,500 held-out test transactions** strictly at the selected threshold **0.60**:

- **Precision**: `0.8814` (88.14%)
- **Recall**: `0.8658` (86.58%)
- **F1-Score**: `0.8736`
- **ROC-AUC**: `0.9924`
- **PR-AUC**: `0.9255`
- **False Positive Rate**: `0.0065` (0.65%)

### Test Confusion Matrix
- **True Positives (TP)**: `342` (Correctly flagged fraud)
- **False Positives (FP)**: `46` (Legitimate flagged)
- **True Negatives (TN)**: `7,059` (Legitimate allowed)
- **False Negatives (FN)**: `53` (Missed fraud)

### Simulated Error Cost at Threshold 0.60 (Simulation Assumptions)
- **Disclaimer**: *Simulation assumptions — not actual Razorpay costs.*
- **Unit FP Cost**: INR 250.00 (Analyst triage + customer friction)
- **Unit FN Cost**: INR 2,500.00 (Chargeback loss & fraud liability)
- **Total False Positive Cost**: INR 11,500.00 (46 FPs)
- **Total False Negative Cost**: INR 132,500.00 (53 FNs)
- **Combined Simulated Error Cost**: **INR 144,000.00**

---

## 7. CLI Usage

```bash
# Train models, run validation grid, and save artifacts to ml/models/
python ml/train_model.py --data data/raw/transactions.csv --output-dir ml/models

# Evaluate chosen detector on the held-out test set (strictly at threshold 0.60)
python ml/evaluate_model.py --data data/raw/transactions.csv --model-dir ml/models --threshold 0.60
```
