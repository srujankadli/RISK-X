# RISK-X Test Suite

Comprehensive automated test suite for backend APIs, ML pipelines, and decision rules.

---

## Directory Structure

```
tests/
├── backend/
│   ├── __init__.py
│   └── test_health.py    # Health endpoint and API availability tests
└── README.md
```

---

## Running Tests

From the project root:

```bash
# Run all tests
pytest

# Run backend unit tests with verbose output
pytest tests/backend/ -v
```
