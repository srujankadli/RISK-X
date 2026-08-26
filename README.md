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
┌──────────────────────────────────────────────┐
│             Incoming Transaction             │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  Validation Layer (Pydantic / Extra-Forbid)  │  ◄── Target leakage elimination
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│       Feature Pipeline & In-Memory RF        │  ◄── Scikit-learn Random Forest
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│       Deterministic Risk Score (0-100)       │  ◄── Half-up mathematical linear mapping
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│          Deterministic Decision Engine       │  ◄── ALLOW (0-39) | REVIEW (40-69) | BLOCK (70-100)
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  Structured Evidence & Explainability Layer  │  ◄── Ranked signals (HIGH/MED/LOW) & Analyst Summary
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│       Analyst Dashboard & Audit Trail        │  ◄── React + Vite Real-Time Cockpit
└──────────────────────────────────────────────┘
```

---

## 3. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend API** | Python 3.10+, FastAPI, Uvicorn, Pydantic | High-performance asynchronous REST API with liveness & readiness probes |
| **Frontend UI** | React 18, Vite | Real-time Analyst Dashboard & Decision Cockpit |
| **Machine Learning** | scikit-learn, NumPy, pandas, joblib | Chronological feature pipelines & Random Forest detector |
| **Testing** | pytest, FastAPI TestClient | Comprehensive backend, ML, engine, and evidence unit tests (114+ tests) |

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
- [x] **Milestone 6: Analyst Dashboard**
  - Interactive React dashboard with scenario presets (`Normal`, `Suspicious`, `High-Risk Attack`), live model inference, and evidence cockpit.

---

## 5. Getting Started

### Prerequisites
- **Python**: 3.10 or higher
- **Node.js**: v18.0.0 or higher
- **npm**: v9.0.0 or higher

### 1. Running the Backend Service
```bash
cd backend
python -m venv venv
# Activate venv:
# Windows (PowerShell): .\venv\Scripts\Activate.ps1
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- **Liveness Probe**: [http://localhost:8000/health](http://localhost:8000/health)
- **Readiness Probe**: [http://localhost:8000/health/ready](http://localhost:8000/health/ready)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Running the Analyst Dashboard
```bash
cd frontend
npm install
npm run dev
```
- **Analyst Dashboard**: [http://localhost:5173](http://localhost:5173)

### 3. Running Automated Tests
From the root directory:
```bash
pytest -v
```
