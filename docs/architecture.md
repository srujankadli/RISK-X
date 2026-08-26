# RISK-X Architecture Specification

## 1. System Philosophy

RISK-X is architected around the core principle that **automated risk mitigation must be both high-precision and strictly accountable**. 

A pure black-box model creates operational blindspots, while pure deterministic rules are brittle against evolving fraud patterns. RISK-X bridges both paradigms:

```
Transaction (Direct API or Razorpay Webhook)
   │
   ▼
[1] Ingestion & Parsing (HMAC-SHA256 Signature Verification & Idempotency Check)
   │
   ▼
[2] Feature Pipeline Transformation (ColumnTransformer & Derived Ratios)
   │
   ▼
[3] Real-time ML Detection (In-Memory Random Forest predicted fraud probability)
   │
   ▼
[4] Deterministic Risk Scoring (Half-Up Linear Mapping to 0 - 100 Integer Score)
   │
   ▼
[5] Guarded Decision Engine (ALLOW: 0-39 / REVIEW: 40-69 / BLOCK: 70-100)
   │
   ▼
[6] Structured Evidence & Explainability Synthesis (Ranked HIGH/MED/LOW + Narrative Summary)
   │
   ▼
[7] Transaction Persistence & Ledger (SQLite WAL Mode, Indexed Storage & Audit Trail)
   │
   ▼
[8] Analyst Dashboard & Real-Time Intelligence (React + Vite Console & Stream)
```

---

## 2. Component Details

### A. Backend Layer (`backend/`)
- Built with **FastAPI** for high-throughput asynchronous request processing.
- Modular architecture with distinct layers for API endpoints, core configuration, in-memory ML inference wrappers, and decision logic.
- Pydantic models for strict data contract enforcement (`extra="forbid"` to eliminate target leakage).

### B. Machine Learning & Preprocessing Layer (`ml/`)
- **Scikit-learn Feature Pipeline**: Imputation, derived behavioral ratios, and standard scaling.
- **ML Classifier**: Random Forest detector trained on chronologically-split historical transactions, outputting predicted fraud probabilities bounded in $[0, 1]$.

### C. Risk Scoring & Decision Engine Layer (`backend/app/engine/`)
- **Scoring Engine**: Maps predicted probability linearly to an integer $[0, 100]$ score using deterministic mathematical half-up rounding and safe float clamping.
- **Decision Engine**: Applies operational policy thresholds:
  - **ALLOW** (0 – 39): Frictionless low-risk processing
  - **REVIEW** (40 – 69): Guarded step-up authentication or analyst triage
  - **BLOCK** (70 – 100): Immediate payment decline

### D. Structured Evidence & Explainability Layer (`backend/app/engine/evidence.py`)
- Extracts structured `EvidenceItem` records based strictly on request-time observable indicators (amount anomalies, payment velocity, failed retries, new device, multi-account device association, location/time flags).
- Deterministically ranks evidence items by severity tier (`HIGH` > `MEDIUM` > `LOW`) and signal priority.
- Synthesizes concise analyst-facing summaries without exposing internal tree nodes or model weights.

### E. Persistence & Webhook Ingestion Layer (`backend/app/db/` & `backend/app/api/v1/webhooks.py`)
- **Storage**: Lightweight SQLite repository with Write-Ahead Logging (`PRAGMA journal_mode=WAL;`), indexing on `transaction_id`, `created_at`, `decision`, and `idempotency_key`.
- **Razorpay Webhooks**: HMAC-SHA256 signature verification via `X-Razorpay-Signature`.
- **Idempotency**: Automatic deduplication against duplicate payment IDs with `idempotent_replay: true`.

### F. Frontend Dashboard (`frontend/`)
- React + Vite Single Page Application designed for speed and real-time visualization.
- Interfaces:
  - Real-Time Transaction Assessment Console (Interactive form & 3 audit presets)
  - Historical Transaction Audit Ledger (Data table, pagination, filter by decision)
  - Razorpay Webhook Ingestion Simulator (Client-side HMAC-SHA256 signature generation)

---

## 3. Security and Compliance Principles
- **Zero Target Leakage**: Model inference strictly forbids ground-truth labels or outcome indicators.
- **Deterministic Action Guardrails**: Automated block actions require strict deterministic threshold verification.
- **Full Auditability**: Every assessment outputs structured evidence, risk score, probability, and decision rationale stored in an indexed SQLite ledger.
