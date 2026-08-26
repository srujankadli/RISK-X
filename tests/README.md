# RISK-X Test Suite

Comprehensive automated test suite covering Backend APIs, ML risk detection pipelines, Deterministic Risk Scoring, Policy Decisioning, Structured Evidence Layer, SQLite Persistence, and Razorpay Webhook Ingestion.

---

## Directory Structure

```
tests/
├── backend/
│   ├── __init__.py
│   └── test_health.py          # Health endpoint & root API availability tests
├── db/
│   ├── __init__.py
│   └── test_database.py        # SQLite schema init, repository CRUD, filtering, & stats tests
├── engine/
│   ├── __init__.py
│   ├── test_scoring.py         # Probability to 0-100 score mapping & validation tests
│   ├── test_decision.py        # ALLOW / REVIEW / BLOCK policy threshold boundary tests
│   ├── test_reasons.py         # Explainable risk signal extractor tests
│   ├── test_evidence.py        # Structured evidence extraction, severity ranking, & summaries
│   └── test_api_integration.py # FastAPI /api/v1/risk/assess and transaction ledger integration tests
├── ml_detector/
│   ├── test_split.py           # Chronological temporal splitting & zero leakage tests
│   ├── test_features.py        # Feature engineering calculations & pipeline tests
│   └── test_model.py           # Probability bounds & classifier tests
├── webhooks/
│   ├── __init__.py
│   └── test_razorpay_webhook.py # HMAC-SHA256 signature verification & idempotency tests
├── conftest.py                 # Isolated temporary test database and path resolution
└── README.md
```

---

## Running Tests

From the project root:

```bash
# Run all tests across backend, engine, ML, database, and webhooks
pytest -v

# Run only Webhook tests
pytest tests/webhooks/ -v

# Run only Database tests
pytest tests/db/ -v

# Run only Risk Engine & Evidence tests
pytest tests/engine/ -v
```
