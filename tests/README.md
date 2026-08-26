# RISK-X Test Suite

Comprehensive automated test suite covering Backend APIs and ML risk detection pipelines.

---

## Directory Structure

```
tests/
├── backend/
│   ├── __init__.py
│   └── test_health.py        # Health endpoint & root API availability tests
├── ml_detector/
│   ├── test_split.py         # Chronological temporal splitting & zero leakage tests
│   ├── test_features.py      # Feature engineering calculations & pipeline tests
│   └── test_model.py         # Probability bounds & classifier tests
├── conftest.py               # Root path resolution
└── README.md
```

---

## Running Tests

From the project root:

```bash
# Run all tests across backend and ML
pytest

# Run tests with verbose output
pytest -v

# Run only ML detector tests
pytest tests/ml_detector/ -v

# Run only Backend tests
pytest tests/backend/ -v
```
