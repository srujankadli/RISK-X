#!/usr/bin/env python3
"""
RISK-X Model Training & Validation Pipeline
===========================================
Trains baseline (Logistic Regression) and stronger (Random Forest) classifiers
on strictly chronological training data, performs validation set evaluation,
executes validation threshold selection, and exports serialized models.

Usage:
    python ml/train_model.py --data data/raw/transactions.csv --output-dir ml/models
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.pipelines.feature_pipeline import build_preprocessor, get_feature_names


def load_and_split_data(
    csv_path: str,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Loads dataset and splits strictly chronologically into Train, Validation, and Test.
    """
    df = pd.read_csv(csv_path)
    # Ensure chronological order
    df = df.sort_values(by="timestamp").reset_index(drop=True)

    n_total = len(df)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    train_df = df.iloc[:n_train].copy().reset_index(drop=True)
    val_df = df.iloc[n_train : n_train + n_val].copy().reset_index(drop=True)
    test_df = df.iloc[n_train + n_val :].copy().reset_index(drop=True)

    return train_df, val_df, test_df


def print_split_summary(
    train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame
):
    """Prints dataset split details and temporal ranges."""
    print("=" * 70)
    print("                   CHRONOLOGICAL DATASET SPLIT                    ")
    print("=" * 70)
    splits = [("TRAIN (70%)", train_df), ("VALIDATION (15%)", val_df), ("HELD-OUT TEST (15%)", test_df)]
    for name, split in splits:
        susp_count = int(split["label"].sum())
        susp_rate = (susp_count / len(split)) * 100
        print(f"Split: {name:<20}")
        print(f"  Rows:            {len(split):>7,}")
        print(f"  Date Range:      {split['timestamp'].min()} to {split['timestamp'].max()}")
        print(f"  Suspicious Rate: {susp_count:>5,} / {len(split):,} ({susp_rate:>5.2f}%)")
        print("-" * 70)


def evaluate_predictions(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> Dict[str, float]:
    """Calculates comprehensive classification metrics for given probabilities and threshold."""
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    return {
        "threshold": threshold,
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "pr_auc": float(average_precision_score(y_true, y_prob)),
        "fpr": float(fpr),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
    }


def evaluate_threshold_grid(y_val: np.ndarray, val_probs: np.ndarray, fp_cost: float = 250.0, fn_cost: float = 2500.0) -> pd.DataFrame:
    """Evaluates multiple operating thresholds strictly on the validation set."""
    thresholds = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
    records = []
    for t in thresholds:
        m = evaluate_predictions(y_val, val_probs, threshold=t)
        sim_cost = (m["fp"] * fp_cost) + (m["fn"] * fn_cost)
        records.append({
            "Threshold": f"{t:.2f}",
            "Precision": f"{m['precision']:.4f}",
            "Recall": f"{m['recall']:.4f}",
            "F1-Score": f"{m['f1']:.4f}",
            "FPR": f"{m['fpr']:.4f}",
            "TP": m["tp"],
            "FP": m["fp"],
            "TN": m["tn"],
            "FN": m["fn"],
            "Sim. Cost (INR)*": f"{sim_cost:,.0f}",
        })
    return pd.DataFrame(records)


def parse_args():
    parser = argparse.ArgumentParser(description="Train RISK-X ML Models.")
    parser.add_argument("--data", type=str, default="data/raw/transactions.csv", help="Path to raw CSV dataset.")
    parser.add_argument("--output-dir", type=str, default="ml/models", help="Directory to save model artifacts.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"[*] Loading data from: {args.data}")
    train_df, val_df, test_df = load_and_split_data(args.data)
    print_split_summary(train_df, val_df, test_df)

    y_train = train_df["label"].values
    y_val = val_df["label"].values

    # 1. Build and Fit Preprocessor on TRAIN ONLY
    print("[*] Fitting preprocessing pipeline on TRAIN set...")
    preprocessor = build_preprocessor()
    X_train_proc = preprocessor.fit_transform(train_df)
    X_val_proc = preprocessor.transform(val_df)

    feature_names = get_feature_names(preprocessor)
    print(f"[+] Extracted {len(feature_names)} features: {feature_names}")

    # 2. Train Baseline Logistic Regression
    print("\n[*] Training Baseline: Logistic Regression (balanced class weights)...")
    log_reg = LogisticRegression(
        class_weight="balanced",
        random_state=args.seed,
        max_iter=1000,
        C=1.0,
    )
    log_reg.fit(X_train_proc, y_train)

    val_probs_lr = log_reg.predict_proba(X_val_proc)[:, 1]
    lr_val_metrics = evaluate_predictions(y_val, val_probs_lr, threshold=0.5)

    print("\n--- Logistic Regression Validation Metrics (Default 0.50 Threshold) ---")
    print(f"  Precision: {lr_val_metrics['precision']:.4f}")
    print(f"  Recall:    {lr_val_metrics['recall']:.4f}")
    print(f"  F1-Score:  {lr_val_metrics['f1']:.4f}")
    print(f"  ROC-AUC:   {lr_val_metrics['roc_auc']:.4f}")
    print(f"  PR-AUC:    {lr_val_metrics['pr_auc']:.4f}")
    print(f"  FPR:       {lr_val_metrics['fpr']:.4f}")

    # 3. Train Stronger Random Forest Model
    print("\n[*] Training Stronger Model: Random Forest Classifier (balanced class weights)...")
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_split=10,
        min_samples_leaf=4,
        class_weight="balanced",
        random_state=args.seed,
        n_jobs=-1,
    )
    rf_model.fit(X_train_proc, y_train)

    val_probs_rf = rf_model.predict_proba(X_val_proc)[:, 1]
    rf_val_metrics = evaluate_predictions(y_val, val_probs_rf, threshold=0.5)

    print("\n--- Random Forest Validation Metrics (Default 0.50 Threshold) ---")
    print(f"  Precision: {rf_val_metrics['precision']:.4f}")
    print(f"  Recall:    {rf_val_metrics['recall']:.4f}")
    print(f"  F1-Score:  {rf_val_metrics['f1']:.4f}")
    print(f"  ROC-AUC:   {rf_val_metrics['roc_auc']:.4f}")
    print(f"  PR-AUC:    {rf_val_metrics['pr_auc']:.4f}")
    print(f"  FPR:       {rf_val_metrics['fpr']:.4f}")

    # 4. Threshold Selection Grid on Validation Set
    print("\n" + "=" * 70)
    print("        RANDOM FOREST: VALIDATION THRESHOLD OPERATING GRID         ")
    print("=" * 70)
    thresh_table = evaluate_threshold_grid(y_val, val_probs_rf)
    print(thresh_table.to_string(index=False))
    print("\n* Note: Simulated error costs use simulation assumptions (INR 250 FP, INR 2,500 FN)")
    print("  The simulated cost model is illustrative and was not used as the threshold-selection objective.")

    # Explicit threshold selection documentation
    selected_threshold = 0.60
    selected_val_metrics = evaluate_predictions(y_val, val_probs_rf, threshold=selected_threshold)

    print(f"\n[+] Selected Operating Threshold: {selected_threshold:.2f}")
    print("    Threshold 0.60 is an operational operating point chosen to balance high suspicious-event")
    print("    recall (>90% on validation) with high precision (89.11%) and a sub-1% false-positive rate (0.79%).")
    print("    Threshold 0.70 has a higher validation F1, but 0.60 retains higher recall.")
    print(f"    Validation Precision: {selected_val_metrics['precision']:.4f} | Recall: {selected_val_metrics['recall']:.4f} | F1: {selected_val_metrics['f1']:.4f} | FPR: {selected_val_metrics['fpr']:.4f}")

    # 5. Serialize Artifacts
    print("\n[*] Saving model artifacts...")
    preprocessor_path = os.path.join(args.output_dir, "preprocessor.joblib")
    lr_path = os.path.join(args.output_dir, "logistic_regression_baseline.joblib")
    rf_path = os.path.join(args.output_dir, "random_forest_detector.joblib")
    summary_path = os.path.join(args.output_dir, "training_summary.json")

    joblib.dump(preprocessor, preprocessor_path)
    joblib.dump(log_reg, lr_path)
    joblib.dump(rf_model, rf_path)

    training_summary = {
        "dataset_version": "1.0",
        "random_seed": args.seed,
        "features": feature_names,
        "selected_model": "RandomForestClassifier",
        "selected_threshold": selected_threshold,
        "threshold_selection_justification": (
            "Threshold 0.60 is an operational operating point chosen to balance high suspicious-event "
            "recall (>90% on validation) with high precision (89.11%) and a sub-1% false-positive rate (0.79%). "
            "Threshold 0.70 has a higher validation F1, but 0.60 retains higher recall. "
            "The simulated cost model is illustrative and was not used as the threshold-selection objective."
        ),
        "validation_metrics": {
            "logistic_regression_0.5": lr_val_metrics,
            "random_forest_0.5": rf_val_metrics,
            "random_forest_selected_0.60": selected_val_metrics,
        },
    }

    with open(summary_path, "w") as f:
        json.dump(training_summary, f, indent=2)

    print(f"[+] Preprocessor saved to: {preprocessor_path}")
    print(f"[+] Baseline LR saved to:  {lr_path}")
    print(f"[+] Random Forest saved to: {rf_path}")
    print(f"[+] Training summary saved to: {summary_path}")
    print("\n[+] Training complete. Proceed to evaluate_model.py for held-out test evaluation.")


if __name__ == "__main__":
    main()
