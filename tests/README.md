# RISK-X Test Suite

Comprehensive automated test suite covering Backend APIs, ML risk detection pipelines, Deterministic Risk Scoring, Policy Decisioning, and the Structured Evidence & Explainability Layer.

---

## Directory Structure

```
tests/
├── backend/
│   ├── __init__.py
│   └── test_health.py          # Health endpoint & root API availability tests
├── engine/
│   ├── __init__.py
│   ├── test_scoring.py         # Probability to 0-100 score mapping & validation tests
│   ├── test_decision.py        # ALLOW / REVIEW / BLOCK policy threshold boundary tests
│   ├── test_reasons.py         # Explainable risk signal extractor tests
│   ├── test_evidence.py        # Structured evidence extraction, severity ranking, & summaries
│   └── test_api_integration.py # FastAPI /api/v1/risk/assess end-to-end integration tests
├── ml_detector/
│   ├── test_split.py           # Chronological temporal splitting & zero leakage tests
│   ├── test_features.py        # Feature engineering calculations & pipeline tests
│   └── test_model.py           # Probability bounds & classifier tests
├── conftest.py                 # Root path resolution
└── README.md
```

---

## Running Tests

From the project root:

```bash
# Run all tests across backend, engine, and ML
pytest

# Run tests with verbose output
pytest -v

# Run only Risk Engine & Evidence tests
pytest tests/engine/ -v

# Run only ML detector tests
pytest tests/ml_detector/ -v

# Run only Backend tests
pytest tests/backend/ -v
```
