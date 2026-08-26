# RISK-X Architecture Specification

## 1. System Philosophy

RISK-X is architected around the core principle that **automated risk mitigation must be both high-precision and strictly accountable**. 

A pure black-box model creates operational blindspots, while pure deterministic rules are brittle against evolving fraud patterns. RISK-X bridges both paradigms:

```
Transaction
   │
   ▼
[1] Ingestion & Parsing (Razorpay Payload Validation)
   │
   ▼
[2] Real-time Detection Layer
   ├── Fast Deterministic Rules (Velocity checks, known bad lists, impossible travel)
   └── ML Risk Classifier (scikit-learn baseline model for anomaly scoring)
   │
   ▼
[3] Investigation Engine
   ├── Behavioral Profiling (Historical baseline deviation)
   └── Graph & Entity Linkage (Shared cards, IPs, device clusters)
   │
   ▼
[4] Evidence Synthesis
   └── Structured Evidence Package (JSON indicators, human-readable reason codes)
   │
   ▼
[5] Calibrated Risk Scoring
   └── Continuous score (0 - 100) + Risk Tier categorization
   │
   ▼
[6] Deterministic Decision Engine
   └── Policy Matrix (ALLOW / STEP_UP_2FA / MANUAL_REVIEW / BLOCK)
   │
   ▼
[7] Guarded Action Execution & Immutable Audit Trail
   └── Execution log with decision rationale stored in DB
```

---

## 2. Component Details

### A. Backend Layer (`backend/`)
- Built with **FastAPI** for high-throughput asynchronous request processing.
- Modular architecture with distinct layers for API endpoints, core configuration, ML inference wrappers, and decision logic.
- Pydantic models for strict data contract enforcement and validation.

### B. Machine Learning & Rules Layer (`ml/`)
- **Deterministic Rules Engine**: Fast pre-screen checks executing in < 5ms.
- **ML Classifier**: Trained on transaction features (amount, time of day, velocity, location disparity) providing calibrated risk probabilities.

### C. Investigation & Evidence Layer (`investigations/`)
- Aggregates multi-dimensional risk factors into an immutable **Evidence Package**.
- Prepares structured data for both human risk analysts and future LLM narrative generation.

### D. Decision Engine & Action Layer
- Translates risk score and critical flags into guarded, deterministic responses:
  - **ALLOW** (0 - 29): Low risk
  - **STEP_UP_2FA** (30 - 69): Elevate authentication
  - **MANUAL_REVIEW** (70 - 89): Escalate to analyst queue
  - **BLOCK** (90 - 100): Terminate payment attempt

### E. Frontend Dashboard (`frontend/`)
- React + Vite Single Page Application designed for speed and real-time visualization.
- Planned interfaces: Live Transaction Stream, Case Investigation View, Rule & Model Performance Metrics.

---

## 3. Security and Compliance Principles
- **No plaintext sensitive card data**: Only BIN (first 6) and last 4 digits are processed/stored.
- **Deterministic action guardrails**: High-impact actions (blocking accounts/merchants) require strict threshold verification and cannot be triggered by unconstrained LLM outputs.
- **Full Auditability**: Every decision records input snapshot, rule triggers, ML score, timestamp, and resulting action.
