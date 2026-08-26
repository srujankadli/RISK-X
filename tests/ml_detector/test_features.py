import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.pipelines.feature_pipeline import (
    FeatureEngineer,
    build_preprocessor,
    get_feature_names,
    ALL_NUMERIC_FEATURES,
)


@pytest.fixture
def sample_transaction_df():
    return pd.DataFrame([
        {
            "transaction_id": "txn_0000001",
            "customer_id": "cust_00001",
            "merchant_id": "merch_0001",
            "amount": 2500.0,
            "timestamp": "2026-06-01T08:00:00Z",
            "device_id": "dev_12345",
            "ip_address": "103.21.10.20",
            "location": "Mumbai",
            "payment_method": "upi",
            "account_age_days": 150,
            "previous_transaction_count": 5,
            "failed_attempts": 0,
            "refund_count": 0,
            "customer_avg_amount": 500.0,
            "transactions_last_10min": 1,
            "transactions_last_1hr": 2,
            "device_account_count": 1,
            "is_new_device": 0,
            "is_unusual_time": 0,
            "is_unusual_location": 0,
            "label": 0,
        },
        {
            "transaction_id": "txn_0000002",
            "customer_id": "cust_00002",
            "merchant_id": "merch_0002",
            "amount": 10000.0,
            "timestamp": "2026-06-01T08:05:00Z",
            "device_id": "dev_54321",
            "ip_address": "157.34.12.34",
            "location": "Delhi NCR",
            "payment_method": "card",
            "account_age_days": 30,
            "previous_transaction_count": 1,
            "failed_attempts": 3,
            "refund_count": 1,
            "customer_avg_amount": 1000.0,
            "transactions_last_10min": 3,
            "transactions_last_1hr": 4,
            "device_account_count": 4,
            "is_new_device": 1,
            "is_unusual_time": 1,
            "is_unusual_location": 1,
            "label": 1,
        },
    ])


def test_feature_engineer_derived_calculations(sample_transaction_df):
    """Verify exact mathematical computation of derived behavioral features."""
    fe = FeatureEngineer()
    transformed = fe.transform(sample_transaction_df)

    # Row 0: amount=2500, cust_avg=500 -> ratio ~ 5.0
    assert np.isclose(transformed.loc[0, "amount_to_customer_avg_ratio"], 5.0, atol=1e-3)
    assert np.isclose(transformed.loc[0, "log_amount"], np.log1p(2500.0))
    # Row 0: tx_10m=1, tx_1h=2 -> ratio = 1 / (2 + 1) = 0.3333
    assert np.isclose(transformed.loc[0, "velocity_ratio"], 1.0 / 3.0, atol=1e-3)
    # Row 0: dev_acct=1, prev_tx=5 -> ratio = 1 / (5 + 1) = 0.1666
    assert np.isclose(transformed.loc[0, "device_reuse_ratio"], 1.0 / 6.0, atol=1e-3)


def test_preprocessing_pipeline_fit_transform(sample_transaction_df):
    """Verify that the full ColumnTransformer runs without errors and produces expected output array."""
    pipeline = build_preprocessor()
    X_proc = pipeline.fit_transform(sample_transaction_df)

    assert isinstance(X_proc, np.ndarray)
    assert X_proc.shape[0] == 2
    # Check that feature names match output columns
    names = get_feature_names(pipeline)
    assert len(names) == X_proc.shape[1]
    assert "amount_to_customer_avg_ratio" in names
    assert "velocity_ratio" in names
    assert "device_reuse_ratio" in names
