#!/usr/bin/env python3
"""
RISK-X Model Evaluation & Cost Simulation Pipeline
==================================================
Evaluates the trained ML risk detector on the strictly HELD-OUT TEST SET (untouched
during training & threshold tuning). Calculates test performance, confusion matrix,
feature importances, and configurable cost simulations strictly at the selected threshold.

Usage:
    python ml/evaluate_model.py --data data/raw/transactions.csv --model-dir ml/models --threshold 0.60
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.pipelines.feature_pipeline import get_feature_names


def load_held_out_test_set(
    csv_path: str,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> pd.DataFrame:
    """Loads dataset and extracts strictly the held-out test split."""
    df = pd.read_csv(csv_path)
    df = df.sort_values(by="timestamp").reset_index(drop=True)
    n_total = len(df)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)
    test_df = df.iloc[n_train + n_val :].copy().reset_index(drop=True)
    return test_df


def compute_cost_model(
    tp: int, fp: int, tn: int, fn: int, fp_cost: float = 250.0, fn_cost: float = 2500.0
) -> Dict[str, float]:
    """Calculates simulated financial error cost under explicit assumption parameters."""
    total_fp_cost = fp * fp_cost
    total_fn_cost = fn * fn_cost
    total_cost = total_fp_cost + total_fn_cost
    return {
        "unit_fp_cost_inr": fp_cost,
        "unit_fn_cost_inr": fn_cost,
        "total_fp_cost_inr": total_fp_cost,
        "total_fn_cost_inr": total_fn_cost,
        "combined_error_cost_inr": total_cost,
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate RISK-X ML Detector on Held-out Test Set.")
    parser.add_argument("--data", type=str, default="data/raw/transactions.csv", help="Path to raw dataset.")
    parser.add_argument("--model-dir", type=str, default="ml/models", help="Directory containing trained models.")
    parser.add_argument("--threshold", type=float, default=0.60, help="Selected decision threshold.")
    parser.add_argument("--fp-cost", type=float, default=250.0, help="Simulated cost per False Positive (INR).")
    parser.add_argument("--fn-cost", type=float, default=2500.0, help="Simulated cost per False Negative (INR).")
    return parser.parse_args()


def main():
    args = parse_args()

    # Load Artifacts
    preprocessor_path = os.path.join(args.model_dir, "preprocessor.joblib")
    rf_path = os.path.join(args.model_dir, "random_forest_detector.joblib")

    if not os.path.exists(preprocessor_path) or not os.path.exists(rf_path):
        print("[-] Model artifacts not found. Please run `python ml/train_model.py` first.")
        sys.exit(1)

    print("[*] Loading preprocessor and trained Random Forest model...")
    preprocessor = joblib.load(preprocessor_path)
    rf_model = joblib.load(rf_path)

    # Load Held-out Test Data
    print(f"[*] Extracting HELD-OUT TEST set from: {args.data}")
    test_df = load_held_out_test_set(args.data)
    y_test = test_df["label"].values

    print(f"    Held-out Test Rows: {len(test_df):,}")
    print(f"    Date Range:         {test_df['timestamp'].min()} to {test_df['timestamp'].max()}")
    print(f"    Suspicious Count:   {int(y_test.sum())} ({y_test.mean()*100:.2f}%)")

    # Transform test set using frozen preprocessor
    X_test_proc = preprocessor.transform(test_df)
    feature_names = get_feature_names(preprocessor)

    # Predict Probabilities
    test_probs_rf = rf_model.predict_proba(X_test_proc)[:, 1]

    # Evaluate at Selected Threshold (Single evaluation pass)
    y_pred_rf = (test_probs_rf >= args.threshold).astype(int)

    precision = float(precision_score(y_test, y_pred_rf, zero_division=0))
    recall = float(recall_score(y_test, y_pred_rf, zero_division=0))
    f1 = float(f1_score(y_test, y_pred_rf, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, test_probs_rf))
    pr_auc = float(average_precision_score(y_test, test_probs_rf))

    tn, fp, fn, tp = confusion_matrix(y_test, y_pred_rf, labels=[0, 1]).ravel()
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    print("\n" + "=" * 70)
    print("           HELD-OUT TEST SET EVALUATION REPORT (EXACT ONCE)        ")
    print("=" * 70)
    print(f"Model Evaluated:              Random Forest Classifier")
    print(f"Operating Decision Threshold: {args.threshold:.2f}")
    print("-" * 70)
    print(f"Precision:                    {precision:.4f} ({precision*100:.2f}%)")
    print(f"Recall:                       {recall:.4f} ({recall*100:.2f}%)")
    print(f"F1-Score:                     {f1:.4f}")
    print(f"ROC-AUC:                      {roc_auc:.4f}")
    print(f"PR-AUC (Avg Precision):       {pr_auc:.4f}")
    print(f"False Positive Rate (FPR):    {fpr:.4f} ({fpr*100:.2f}%)")
    print("-" * 70)
    print("CONFUSION MATRIX:")
    print(f"  True Positives  (TP): {tp:>5,}  (Correctly detected suspicious)")
    print(f"  False Positives (FP): {fp:>5,}  (Legitimate flagged as suspicious)")
    print(f"  True Negatives  (TN): {tn:>5,}  (Legitimate allowed)")
    print(f"  False Negatives (FN): {fn:>5,}  (Missed suspicious)")
    print("-" * 70)

    # Cost Simulation at chosen threshold
    cost_metrics = compute_cost_model(tp, fp, tn, fn, fp_cost=args.fp_cost, fn_cost=args.fn_cost)
    print("SIMULATED ERROR COST ANALYSIS (Simulation assumptions — not actual Razorpay costs):")
    print(f"  Assumed Cost per FP:        INR {cost_metrics['unit_fp_cost_inr']:,.2f} (Analyst triage + user drop-off)")
    print(f"  Assumed Cost per FN:        INR {cost_metrics['unit_fn_cost_inr']:,.2f} (Chargeback & fraud loss)")
    print(f"  Total False Positive Cost:  INR {cost_metrics['total_fp_cost_inr']:,.2f} ({fp} FPs)")
    print(f"  Total False Negative Cost:  INR {cost_metrics['total_fn_cost_inr']:,.2f} ({fn} FNs)")
    print(f"  Combined Error Cost:        INR {cost_metrics['combined_error_cost_inr']:,.2f}")
    print("-" * 70)

    # Feature Importance
    importances = rf_model.feature_importances_
    feat_imp = pd.DataFrame({
        "feature": feature_names,
        "importance": importances,
    }).sort_values(by="importance", ascending=False).reset_index(drop=True)

    print("TOP MODEL-ASSOCIATED PREDICTIVE FEATURES (Feature Importance):")
    for rank, row in feat_imp.head(10).iterrows():
        print(f"  {rank+1:>2}. {row['feature']:<32} {row['importance']:.4f} ({row['importance']*100:.2f}%)")
    print("=" * 70)

    # Export Evaluation Results to JSON
    eval_results = {
        "model": "RandomForestClassifier",
        "threshold": args.threshold,
        "metrics": {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
            "fpr": fpr,
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn),
        },
        "cost_simulation": {
            "disclaimer": "Simulation assumptions — not actual Razorpay costs.",
            **cost_metrics,
        },
        "feature_importances": feat_imp.to_dict(orient="records"),
    }

    eval_json_path = os.path.join(args.model_dir, "evaluation_metrics.json")
    with open(eval_json_path, "w") as f:
        json.dump(eval_results, f, indent=2)

    print(f"\n[+] Machine-readable evaluation results saved to: {eval_json_path}")


if __name__ == "__main__":
    main()
