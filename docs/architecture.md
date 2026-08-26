# RISK-X Architecture Specification

## 1. System Philosophy

RISK-X is architected around the core principle that **automated risk mitigation must be both high-precision and strictly accountable**. 

A pure black-box model creates operational blindspots, while pure deterministic rules are brittle against evolving fraud patterns. RISK-X bridges both paradigms:

```
Transaction
   │
   ▼
[1] Ingestion & Parsing (FastAPI Payload Validation & Extra-Field Prohibition)
   │
   ▼
[2] Real-time Detection Layer
   └── ML Risk Classifier (Random Forest predicting fraud probabilities)
   │
   ▼
[3] Deterministic Risk Scoring
   └── Continuous score (0 - 100) + Risk Level Tier (LOW, MEDIUM, HIGH)
   │
   ▼
[4] Deterministic Decision Engine
   └── Guarded Policy Matrix (ALLOW: 0-39 / REVIEW: 40-69 / BLOCK: 70-100)
   │
   ▼
[5] Structured Evidence & Explainability Synthesis
   ├── Observable Evidence Items (Ranked by severity: HIGH, MEDIUM, LOW)
   ├── Backward-compatible Reason Strings
   └── Concise Analyst Narrative Summary
   │
   ▼
[6] Response & Immutable Audit Trail
   └── Execution payload with full decision rationale
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

### E. Frontend Dashboard (`frontend/`)
- React + Vite Single Page Application designed for speed and real-time visualization.
- Planned interfaces: Live Transaction Stream, Case Investigation View, Rule & Model Performance Metrics.

---

## 3. Security and Compliance Principles
- **Zero Target Leakage**: Model inference strictly forbids ground-truth labels or outcome indicators.
- **Deterministic action guardrails**: Automated block actions require strict deterministic threshold verification.
- **Full Auditability**: Every assessment outputs structured evidence, risk score, probability, and decision rationale.
