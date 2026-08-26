# RISK-X (Risk Investigation System X)

> **AI-Powered Payment Risk Investigation and Response System**  
> Developed for the Razorpay Buildathon | Target Delivery: September 5, 2026

---

## 1. Overview

**RISK-X** is an intelligent payment risk detection, investigation, and decisioning system designed to identify fraudulent transactions, assemble structured evidence, calculate transparent risk scores, and execute deterministic, guarded mitigation actions with complete auditability.

Unlike traditional black-box fraud scoring systems, RISK-X pairs fast statistical / machine learning detection with deep, explainable investigation, structured observable evidence, and guardrailed action recommendations.

---

## 2. Core Architecture

The end-to-end transaction processing pipeline follows this workflow:

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

## 3. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend API** | Python 3.10+, FastAPI, Uvicorn, Pydantic | High-performance asynchronous REST API with liveness & readiness probes |
| **Persistence** | SQLite (Python 3 stdlib), WAL Journal Mode | Thread-safe, zero-dependency transaction ledger and idempotency store (`data/risk_x.db`) |
| **Frontend UI** | React 18, Vite | Real-time Analyst Dashboard, Audit Ledger, & Webhook Simulator |
| **Machine Learning** | scikit-learn, NumPy, pandas, joblib | Chronological feature pipelines & Random Forest detector |
| **Testing** | pytest, FastAPI TestClient | Comprehensive backend, ML, engine, database, and webhook test suite (127 tests) |

---

## 4. Completed Milestones

- [x] **Milestone 1: Project Foundation & Synthetic Dataset Generator** (`f127094`)
  - Realistic transaction generation with stateful counters, opaque device IDs, and 6 fraud scenarios.
- [x] **Milestone 2: ML Risk Detector** (`ca6b4b2`)
  - Chronological 70/15/15 temporal splitting, Random Forest classifier, and single-pass held-out test evaluation.
- [x] **Milestone 3: Risk Scoring & Decision Engine** (`d3c07fd`)
  - Deterministic $[0, 100]$ scoring, `ALLOW` / `REVIEW` / `BLOCK` policy thresholds, and backward-compatible reason strings.
- [x] **Milestone 4: Production Inference Workflow** (`4f91daa`)
  - In-memory model caching, decoupled liveness (`/health`) and readiness (`/health/ready`) probes, zero target leakage (`extra="forbid"`).
- [x] **Milestone 5: Evidence & Explainability Layer** (`126dd9e`)
  - Structured `EvidenceItem` records with severity ranking (`HIGH`, `MEDIUM`, `LOW`) and analyst narrative synthesis.
- [x] **Milestone 6: Analyst Dashboard** (`2668d28`)
  - Interactive React dashboard with scenario presets (`Normal`, `Suspicious`, `High-Risk Attack`), live model inference, and evidence cockpit.
- [x] **Milestone 7: End-to-End Demo Hardening** (`625894d`)
  - Full-stack journey verification and preset alignment to real backend operating points.
- [x] **Milestone 8: Real Transaction Intelligence** (`bb71f85`)
  - SQLite transaction persistence in WAL mode, Razorpay webhook ingestion with HMAC-SHA256 verification and atomic idempotency deduplication, audit ledger APIs, and live KPI stats.

---

## 5. Getting Started & Demo Quickstart

### Prerequisites
- **Python**: 3.10 or higher
- **Node.js**: v18.0.0 or higher
- **npm**: v9.0.0 or higher

### 1. Reset / Seed the Demo Database
RISK-X includes a safe seeding utility that runs realistic transactions through the live ML engine:

```powershell
# Windows:
.\backend\venv\Scripts\python backend/scripts/seed_demo_data.py

# Linux / macOS:
python backend/scripts/seed_demo_data.py
```
*(To start with a completely empty database, use `python backend/scripts/seed_demo_data.py --clean`)*.

### 2. Running the Backend Service
From the repository root:
```powershell
# Windows:
.\backend\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Linux / macOS:
source backend/venv/bin/activate
uvicorn app.main:app --reload --port 8000
```
- **Liveness Probe**: [http://localhost:8000/health](http://localhost:8000/health)
- **Readiness Probe**: [http://localhost:8000/health/ready](http://localhost:8000/health/ready)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Transaction Ledger API**: [http://localhost:8000/api/v1/transactions](http://localhost:8000/api/v1/transactions)
- **Risk Statistics API**: [http://localhost:8000/api/v1/transactions/stats](http://localhost:8000/api/v1/transactions/stats)

### 3. Running the Analyst Dashboard
From a separate terminal in the repository root:
```bash
cd frontend
npm install
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser.

### 4. Running Automated Tests
From the repository root:
```powershell
.\backend\venv\Scripts\pytest -v
```

---

## 6. Demonstration Workflow

1. Open **[http://localhost:5173](http://localhost:5173)**.
2. Verify top right status displays **`ML Detector Online`**.
3. **Assessment Console Tab**:
   - Click **`🟢 Normal Transaction`** $\rightarrow$ **`Run Real-Time Risk Assessment`** $\rightarrow$ Observe **`ALLOW`** (Risk Score: 1).
   - Click **`🟡 Suspicious Activity`** $\rightarrow$ **`Run Real-Time Risk Assessment`** $\rightarrow$ Observe **`REVIEW`** (Risk Score: 67, 3 evidence signals).
   - Click **`🔴 High-Risk Attack Cluster`** $\rightarrow$ **`Run Real-Time Risk Assessment`** $\rightarrow$ Observe **`BLOCK`** (Risk Score: 93, 7 severity-ranked signals).
4. **Audit Ledger Tab**:
   - Inspect historical transaction feed, filter by `ALLOW`, `REVIEW`, or `BLOCK`, and click **`Inspect →`** to load any past transaction into the investigation cockpit.
5. **Razorpay Webhooks Tab**:
   - Transmit a signed webhook event to `/api/v1/webhooks/razorpay` $\rightarrow$ Observe instant HMAC-SHA256 signature verification and risk evaluation.
   - Click **Send** again with the same payment ID $\rightarrow$ Observe **`IDEMPOTENT REPLAY`** without redundant model inference.
