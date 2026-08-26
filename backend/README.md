# RISK-X Backend Service

FastAPI-powered asynchronous backend service for RISK-X payment risk investigation and response.

---

## Directory Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── risk.py         # POST /api/v1/risk/assess & GET /api/v1/risk/readiness
│   │       ├── webhooks.py     # POST /api/v1/webhooks/razorpay (HMAC SHA-256 verification & idempotency)
│   │       └── transactions.py # GET /api/v1/transactions & GET /api/v1/transactions/stats
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Application settings, DB paths, CORS, webhook secrets
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py         # SQLite connection manager, WAL mode, schema init
│   │   └── repository.py       # Transaction repository, filtering, pagination, stats
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── scoring.py          # Deterministic 0-100 risk scoring
│   │   ├── decision.py         # ALLOW / REVIEW / BLOCK decision engine
│   │   ├── reasons.py          # Observable explainable risk signals (string list)
│   │   ├── evidence.py         # Structured, ranked evidence signals & analyst summary
│   │   └── service.py          # RiskEngineService coordinator & model lifecycle
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── risk.py             # Request & Response Pydantic models with structured evidence
│   │   └── webhook.py          # Webhook payload, history items, and stats schemas
│   ├── __init__.py
│   └── main.py                 # Application entrypoint with liveness & readiness probes
├── scripts/
│   └── seed_demo_data.py       # Reset & seed SQLite database with realistic evaluated transactions
├── requirements.txt            # Python dependencies
└── README.md
```

---

## Setup & Running

### 1. Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize / Seed Demo Database
```bash
# Seed curated realistic transactions evaluated through the live model
python scripts/seed_demo_data.py

# Or reset to a clean, empty database:
python scripts/seed_demo_data.py --clean
```

### 4. Start the Backend Server
```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Core Endpoints & Probes
- **Liveness Probe**: `GET http://localhost:8000/health` (Checks if API process is running)
- **Readiness Probe**: `GET http://localhost:8000/health/ready` or `GET http://localhost:8000/ready` (Verifies ML model & preprocessor artifacts are loaded into memory)
- **Root Info**: `GET http://localhost:8000/`
- **Real-Time Risk Assessment**: `POST http://localhost:8000/api/v1/risk/assess`
- **Razorpay Webhook Ingestion**: `POST http://localhost:8000/api/v1/webhooks/razorpay` (HMAC SHA-256 verified)
- **Transaction Ledger & History**: `GET http://localhost:8000/api/v1/transactions`
- **Transaction Detail**: `GET http://localhost:8000/api/v1/transactions/{transaction_id}`
- **Risk Aggregate Statistics**: `GET http://localhost:8000/api/v1/transactions/stats`
- **Engine Readiness**: `GET http://localhost:8000/api/v1/risk/readiness`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Razorpay Webhook Ingestion Contract

### Header Requirements
- `Content-Type: application/json`
- `X-Razorpay-Signature`: Hex-encoded HMAC-SHA256 digest of raw request payload computed using `RAZORPAY_WEBHOOK_SECRET`.

### Webhook Event Example
```json
{
  "entity": "event",
  "account_id": "acc_buildathon_01",
  "event": "payment.authorized",
  "contains": ["payment"],
  "payload": {
    "payment": {
      "entity": {
        "id": "pay_demo_7821",
        "amount": 350000,
        "currency": "INR",
        "status": "authorized",
        "method": "card",
        "notes": {
          "customer_id": "cust_hook_7821",
          "customer_avg_amount": "1400.0",
          "account_age_days": "60",
          "previous_transaction_count": "5",
          "failed_attempts": "1",
          "is_new_device": "1",
          "is_unusual_time": "1"
        }
      }
    }
  }
}
```

### Response: `200 OK`
```json
{
  "status": "processed",
  "event": "payment.authorized",
  "payment_id": "pay_demo_7821",
  "transaction_id": "pay_demo_7821",
  "amount_inr": 3500.0,
  "decision": "REVIEW",
  "risk_score": 67,
  "risk_level": "MEDIUM",
  "fraud_probability": 0.6688,
  "idempotent_replay": false,
  "reasons": [
    "Risk signal: transaction amount is significantly above customer historical average (2.5x higher).",
    "Risk signal: previous failed payment attempt recorded prior to authorization.",
    "Risk signal: payment initiated from an unrecognized/new device.",
    "Risk signal: transaction initiated during atypical customer activity hours."
  ],
  "evidence": [
    {
      "code": "NEW_DEVICE",
      "severity": "MEDIUM",
      "title": "Unrecognized Device Fingerprint",
      "description": "Payment initiated from a previously unseen device fingerprint for this customer account.",
      "observed_value": 1,
      "reference_threshold": "Device first observed = 1"
    }
  ],
  "analyst_summary": "Transaction evaluated with risk score 67 triggering policy REVIEW. Detected 3 risk signals driven primarily by unrecognized device fingerprint."
}
```

---

## Production Guarantees & Features

1. **Idempotency & Deduplication**: Webhooks with identical `payment.id` or `idempotency_key` safely return the cached assessment with `idempotent_replay: true` without duplicate scoring or database row duplication.
2. **Zero External DB Dependency**: Built on SQLite standard library with WAL mode (`PRAGMA journal_mode=WAL;`), indexing, and thread-safe connection pooling.
3. **Model Lifecycle & Caching**: Artifacts are loaded into memory once on first demand and reused across all subsequent requests. No disk reads or model training occur during transaction evaluation.
4. **Zero Target Leakage**: `TransactionAssessmentRequest` forbids extra fields (`model_config = ConfigDict(extra="forbid")`), rejecting requests containing `label` or `is_fraud` with HTTP 422.
5. **Structured Evidence & Ranking**: Observable signals are extracted, classified into severity tiers (`HIGH`, `MEDIUM`, `LOW`), and sorted deterministically.
6. **Resilience**: If model files are missing or corrupted, the service returns HTTP 503 `Service Unavailable` with diagnostic error details.

---

## Running Tests
From the root directory:
```bash
pytest -v
```
