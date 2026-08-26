import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.pipelines.feature_pipeline import build_preprocessor
from sklearn.ensemble import RandomForestClassifier


@pytest.fixture
def mini_train_data():
    np.random.seed(42)
    n = 200
    df = pd.DataFrame({
        "transaction_id": [f"txn_{i:07d}" for i in range(n)],
        "customer_id": [f"cust_{i%20:05d}" for i in range(n)],
        "merchant_id": [f"merch_{i%10:04d}" for i in range(n)],
        "amount": np.random.uniform(50, 5000, n),
        "timestamp": [f"2026-06-01T{i%24:02d}:00:00Z" for i in range(n)],
        "device_id": [f"dev_{i%30:05d}" for i in range(n)],
        "ip_address": ["103.21.1.1"] * n,
        "location": ["Mumbai"] * n,
        "payment_method": np.random.choice(["upi", "card", "netbanking", "wallet"], n),
        "account_age_days": np.random.randint(10, 500, n),
        "previous_transaction_count": np.random.randint(0, 20, n),
        "failed_attempts": np.random.choice([0, 1, 2, 3], n, p=[0.8, 0.1, 0.05, 0.05]),
        "refund_count": [0] * n,
        "customer_avg_amount": np.random.uniform(200, 2000, n),
        "transactions_last_10min": np.random.choice([0, 1, 2], n, p=[0.85, 0.1, 0.05]),
        "transactions_last_1hr": np.random.choice([0, 1, 2, 3], n, p=[0.7, 0.15, 0.1, 0.05]),
        "device_account_count": np.random.choice([1, 2, 3], n, p=[0.8, 0.15, 0.05]),
        "is_new_device": np.random.choice([0, 1], n, p=[0.9, 0.1]),
        "is_unusual_time": np.random.choice([0, 1], n, p=[0.8, 0.2]),
        "is_unusual_location": np.random.choice([0, 1], n, p=[0.9, 0.1]),
        "label": np.random.choice([0, 1], n, p=[0.92, 0.08]),
    })
    return df


def test_model_training_and_probability_bounds(mini_train_data):
    """Verify model fits on preprocessed features and produces output probabilities bounded in [0, 1]."""
    preprocessor = build_preprocessor()
    X_train = preprocessor.fit_transform(mini_train_data)
    y_train = mini_train_data["label"].values

    clf = RandomForestClassifier(n_estimators=20, max_depth=5, random_state=42)
    clf.fit(X_train, y_train)

    probs = clf.predict_proba(X_train)[:, 1]
    assert len(probs) == len(mini_train_data)
    assert np.all(probs >= 0.0)
    assert np.all(probs <= 1.0)
    assert not np.isnan(probs).any()
