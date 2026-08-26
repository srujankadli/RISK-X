# RISK-X (Risk Investigation System X)

> **AI-Powered Payment Risk Investigation and Response System**  
> Developed for the Razorpay Buildathon | Target Delivery: September 5, 2026

---

## 1. Overview

**RISK-X** is an intelligent payment risk detection, investigation, and decisioning system designed to identify fraudulent transactions, assemble structured evidence, calculate transparent risk scores, and execute deterministic, guarded mitigation actions with complete auditability.

Unlike traditional black-box fraud scoring systems, RISK-X pairs fast statistical / machine learning detection with deep, explainable investigation and guardrailed action recommendations.

---

## 2. Core Problem Statement

Modern payment gateways process millions of transactions with complex fraud patterns:
- **Card-Not-Present (CNP) Fraud & Velocity Spikes**: Rapid repeated transactions across synthetic IDs.
- **Account Takeover & Device Spoofing**: Inconsistent device fingerprints, sudden location hops, and atypical behavioral patterns.
- **Black-Box Opacity**: Traditional rule engines and ML classifiers often produce scores without explainable evidence, overwhelming human risk analysts.
- **Uncoordinated Response**: Delayed or overly aggressive interventions (e.g. indiscriminate merchant freezes) cause false positives and customer friction.

**RISK-X solves this by:**
1. Detecting anomalies in real time via ML and deterministic rules.
2. Generating structured evidence packages for flagged transactions.
3. Providing clear, human-understandable explanations for why a transaction is risky.
4. Enforcing deterministic decision guardrails before triggering actions (e.g., allow, step-up 2FA, flag for manual review, block).
5. Maintaining an immutable audit trail for compliance and post-incident review.

---

## 3. Planned Architecture

The end-to-end transaction processing pipeline follows this workflow:

```
┌─────────────────────────┐
│   Incoming Transaction  │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│     Detection Layer     │  ◄── ML Anomaly Detection (scikit-learn) + Deterministic Rules
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Investigation Engine  │  ◄── Graph Linkages & Behavioral Pattern Extraction
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│     Evidence Package    │  ◄── Synthesized Indicators (Velocity, Device, Geolocation)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│    Risk Scoring (0-100) │  ◄── Calibrated Risk Score + Confidence Interval
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Deterministic Engine  │  ◄── Strict Guardrails & Policy Matrix
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Recommended Action    │  ◄── ALLOW | STEP_UP_2FA | MANUAL_REVIEW | BLOCK
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│    Audit Trail & Logs   │  ◄── Immutable Event Record for Compliance
└─────────────────────────┘
```

---

## 4. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend API** | Python 3.10+, FastAPI, Uvicorn | High-performance asynchronous REST API |
| **Frontend UI** | React 18 / 19, Vite, Tailwind CSS | Clean, real-time risk dashboard |
| **Machine Learning** | scikit-learn, NumPy, pandas | Anomaly detection and fraud classification |
| **Database** | SQLite (Initial) / PostgreSQL (Production) | Transaction storage, evidence logs, audit trail |
| **Graph Analysis** | NetworkX (Planned) | Multi-entity linkage & identity ring detection |
| **Explanation / LLM** | Local / Cloud LLM (Planned) | Evidence synthesis and natural language summaries |
| **Visualization** | Recharts (Planned) | Real-time risk distribution & investigation charts |

---

## 5. Repository Structure

```
RISK-X/
├── backend/            # FastAPI backend service
│   ├── app/            # Application source code
│   │   ├── api/        # Endpoint routers
│   │   ├── core/       # Configurations & environment
│   │   └── main.py     # FastAPI application entrypoint
│   ├── requirements.txt # Python dependencies
│   └── README.md
├── frontend/           # React + Vite frontend application
│   ├── src/            # Components, pages, assets
│   ├── package.json    # Frontend dependencies and scripts
│   └── README.md
├── ml/                 # Machine learning models and training pipelines
│   ├── models/         # Serialized model artifacts (.pkl, .joblib)
│   ├── pipelines/      # Preprocessing and feature engineering scripts
│   └── README.md
├── data/               # Datasets and schemas
│   ├── raw/            # Raw transaction datasets
│   ├── processed/      # Cleaned and engineered feature datasets
│   └── README.md
├── investigations/     # Investigation workflow definitions & evidence schemas
│   └── README.md
├── tests/              # Backend, ML, and integration tests
│   ├── backend/        # Unit & API tests for FastAPI
│   └── README.md
├── docs/               # Architecture diagrams, specifications, and notes
│   ├── architecture.md
│   └── roadmap.md
├── .gitignore          # Git ignore rules
└── README.md           # Root documentation
```

---

## 6. Milestone Plan (Incremental Delivery)

- [x] **Milestone 1: Project Foundation** *(Current Step)*
  - Establish modular repository structure
  - Set up FastAPI backend skeleton with `/health` endpoint
  - Set up minimal React + Vite frontend scaffolding
  - Define root documentation and architecture specifications
- [ ] **Milestone 2: Data Modeling & Synthetic Dataset Generator**
  - Define payment transaction schema (Razorpay-compatible)
  - Implement synthetic transaction generator with fraud patterns (velocity spikes, card testing, location anomaly)
- [ ] **Milestone 3: Baseline Detection & Risk Scoring (ML + Rules)**
  - Implement deterministic rule engine (velocity, amounts, geofence)
  - Train baseline scikit-learn anomaly / classification model
  - Create scoring pipeline combining rule flags and ML probabilities
- [ ] **Milestone 4: Investigation Engine & Evidence Synthesis**
  - Implement entity linkage and investigation case builder
  - Generate structured evidence packages
  - Add deterministic decision engine for guarded actions
- [ ] **Milestone 5: Interactive Risk Dashboard (React)**
  - Live transaction stream view
  - Case investigation drilldown with evidence cards and risk gauges
  - Manual review triage controls
- [ ] **Milestone 6: AI Evidence Synthesis & Final Hardening**
  - Integrate LLM agent for plain-language risk explanations
  - Complete end-to-end integration tests and audit logging
  - Buildathon presentation preparation

---

## 7. Getting Started

### Prerequisites
- **Python**: 3.10 or higher
- **Node.js**: v18.0.0 or higher
- **npm**: v9.0.0 or higher

### Running the Backend
```bash
cd backend
python -m venv venv
# Activate venv:
# Windows (PowerShell): .\venv\Scripts\Activate.ps1
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Verify at: [http://localhost:8000/health](http://localhost:8000/health)  
Interactive API docs at: [http://localhost:8000/docs](http://localhost:8000/docs)

### Running the Frontend
```bash
cd frontend
npm install
npm run dev
```
Access UI at: [http://localhost:5173](http://localhost:5173)
