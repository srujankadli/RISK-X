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
│   │       └── risk.py         # POST /api/v1/risk/assess & GET /api/v1/risk/readiness
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Application settings & CORS
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── scoring.py          # Deterministic 0-100 risk scoring
│   │   ├── decision.py         # ALLOW / REVIEW / BLOCK decision engine
│   │   ├── reasons.py          # Observable explainable risk signals
│   │   └── service.py          # RiskEngineService coordinator & model lifecycle
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── risk.py             # Request & Response Pydantic models with strict validation
│   ├── __init__.py
│   └── main.py                 # Application entrypoint with liveness & readiness probes
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

### 3. Start the Backend Server
```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Core Endpoints & Probes
- **Liveness Probe**: `GET http://localhost:8000/health` (Checks if API process is running)
- **Readiness Probe**: `GET http://localhost:8000/health/ready` or `GET http://localhost:8000/ready` (Verifies ML model & preprocessor artifacts are loaded into memory)
- **Root Info**: `GET http://localhost:8000/`
- **Real-Time Risk Assessment**: `POST http://localhost:8000/api/v1/risk/assess`
- **Engine Readiness**: `GET http://localhost:8000/api/v1/risk/readiness`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Risk Assessment API Contract

### Request: `POST /api/v1/risk/assess`
```json
{
  "transaction_id": "txn_sample_001",
  "customer_id": "cust_0001",
  "amount": 25000.0,
  "payment_method": "card",
  "account_age_days": 15,
  "previous_transaction_count": 1,
  "failed_attempts": 2,
  "refund_count": 0,
  "customer_avg_amount": 1200.0,
  "transactions_last_10min": 2,
  "transactions_last_1hr": 3,
  "device_account_count": 3,
  "is_new_device": 1,
  "is_unusual_time": 1,
  "is_unusual_location": 1
}
```

### Response: `200 OK`
```json
{
  "risk_score": 82,
  "fraud_probability": 0.8214,
  "decision": "BLOCK",
  "risk_level": "HIGH",
  "reasons": [
    "Risk signal: transaction amount is significantly above customer historical average (20.8x higher).",
    "Risk signal: high transaction velocity detected (2 payments in the last 10 minutes).",
    "Risk signal: multiple failed payment attempts detected (2 failed attempts prior to authorization).",
    "Risk signal: payment initiated from an unrecognized/new device.",
    "Risk signal: device is associated with multiple customer accounts (3 accounts observed).",
    "Risk signal: unusual transaction location detected outside typical customer operating regions.",
    "Risk signal: transaction initiated during atypical customer activity hours."
  ],
  "transaction_id": "txn_sample_001"
}
```

---

## Production Inference Workflow & Guarantees

1. **Model Lifecycle & Caching**: Artifacts are loaded into memory once on first demand and reused across all subsequent requests. No disk reads or model training occur during transaction evaluation.
2. **Zero Target Leakage**: `TransactionAssessmentRequest` forbids extra fields (`model_config = ConfigDict(extra="forbid")`), rejecting requests containing `label` or `is_fraud` with HTTP 422.
3. **Resilience**: If model files are missing or corrupted, the service returns HTTP 503 `Service Unavailable` with diagnostic error details rather than returning fallback or fake scores.
4. **Latency Profile**: ~23 ms in local FastAPI TestClient benchmark (this measures in-process computation including payload schema validation, feature transformation, Random Forest scoring, and policy decisioning; it does not represent production network latency).

---

## Running Tests
From the root directory:
```bash
# Run all backend and engine unit tests
pytest tests/backend/ tests/engine/ -v
```
