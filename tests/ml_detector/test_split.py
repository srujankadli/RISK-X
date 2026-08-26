import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.train_model import load_and_split_data


@pytest.fixture
def dataset_path():
    return str(ROOT_DIR / "data" / "raw" / "transactions.csv")


def test_temporal_split_sizes(dataset_path):
    """Verify that 70% train, 15% val, and 15% test splits sum exactly to total rows."""
    train_df, val_df, test_df = load_and_split_data(dataset_path)

    total_rows = len(train_df) + len(val_df) + len(test_df)
    assert total_rows == 50000
    assert len(train_df) == 35000
    assert len(val_df) == 7500
    assert len(test_df) == 7500


def test_no_temporal_overlap_and_monotonicity(dataset_path):
    """Verify strictly monotonic chronological separation between train, val, and test splits."""
    train_df, val_df, test_df = load_and_split_data(dataset_path)

    train_max_time = pd.to_datetime(train_df["timestamp"]).max()
    val_min_time = pd.to_datetime(val_df["timestamp"]).min()
    val_max_time = pd.to_datetime(val_df["timestamp"]).max()
    test_min_time = pd.to_datetime(test_df["timestamp"]).min()

    assert train_max_time <= val_min_time, "Train timestamps overlap with Validation"
    assert val_max_time <= test_min_time, "Validation timestamps overlap with Test"


def test_no_transaction_id_leakage_across_splits(dataset_path):
    """Verify zero overlap of transaction IDs between splits."""
    train_df, val_df, test_df = load_and_split_data(dataset_path)

    train_ids = set(train_df["transaction_id"])
    val_ids = set(val_df["transaction_id"])
    test_ids = set(test_df["transaction_id"])

    assert len(train_ids.intersection(val_ids)) == 0
    assert len(train_ids.intersection(test_ids)) == 0
    assert len(val_ids.intersection(test_ids)) == 0
