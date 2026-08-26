"""
Feature Engineering and Preprocessing Pipeline for RISK-X ML Detector
======================================================================
Constructs derived behavioral risk features and builds a reproducible
scikit-learn ColumnTransformer / Pipeline.
"""

from typing import List, Tuple
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer


# Non-predictive metadata / raw string identifier columns to exclude from modeling
EXCLUDE_COLUMNS = [
    "transaction_id",
    "customer_id",
    "merchant_id",
    "device_id",
    "ip_address",
    "timestamp",
    "location",
    "label",
]

RAW_NUMERIC_FEATURES = [
    "amount",
    "account_age_days",
    "previous_transaction_count",
    "failed_attempts",
    "refund_count",
    "customer_avg_amount",
    "transactions_last_10min",
    "transactions_last_1hr",
    "device_account_count",
    "is_new_device",
    "is_unusual_time",
    "is_unusual_location",
]

DERIVED_FEATURES = [
    "amount_to_customer_avg_ratio",
    "log_amount",
    "velocity_ratio",
    "device_reuse_ratio",
]

CATEGORICAL_FEATURES = ["payment_method"]

ALL_NUMERIC_FEATURES = RAW_NUMERIC_FEATURES + DERIVED_FEATURES


class FeatureEngineer(BaseEstimator, TransformerMixin):
    """Generates derived behavioral features from observable transaction state."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X_df = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)

        # 1. Ratio of current amount to historical customer average
        X_df["amount_to_customer_avg_ratio"] = X_df["amount"] / (
            X_df["customer_avg_amount"] + 1e-5
        )

        # 2. Log-transformed amount for scale normalization
        X_df["log_amount"] = np.log1p(X_df["amount"])

        # 3. Short-term velocity intensity ratio (10min vs 1hr)
        X_df["velocity_ratio"] = X_df["transactions_last_10min"] / (
            X_df["transactions_last_1hr"] + 1.0
        )

        # 4. Device cross-account sharing ratio relative to customer history
        X_df["device_reuse_ratio"] = X_df["device_account_count"] / (
            X_df["previous_transaction_count"] + 1.0
        )

        return X_df


def build_preprocessor() -> Pipeline:
    """
    Builds the full scikit-learn preprocessing pipeline.
    Combines feature engineering, median imputation, standard scaling, and one-hot encoding.
    """
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )

    column_preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, ALL_NUMERIC_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )

    pipeline = Pipeline(
        steps=[
            ("feature_engineer", FeatureEngineer()),
            ("preprocessor", column_preprocessor),
        ]
    )

    return pipeline


def get_feature_names(preprocessor: Pipeline) -> List[str]:
    """Retrieves human-readable feature names after transformation."""
    col_transformer: ColumnTransformer = preprocessor.named_steps["preprocessor"]
    cat_encoder = col_transformer.named_transformers_["cat"].named_steps["onehot"]
    cat_cols = cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES).tolist()
    return ALL_NUMERIC_FEATURES + cat_cols
