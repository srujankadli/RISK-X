# RISK-X Investigations Engine

This directory defines the case management, evidence synthesis schemas, and deterministic decision rules.

---

## Core Investigation Pipeline

```
Flagged Transaction
       │
       ▼
Evidence Gathering (Rule triggers, Feature anomalies, Identity clusters)
       │
       ▼
Evidence Package Synthesis (Structured JSON with Confidence & Reason Codes)
       │
       ▼
Risk Score Calculation (0 - 100)
       │
       ▼
Deterministic Policy Engine (Guarded thresholds)
       │
       ▼
Action Recommendation & Audit Log
```

---

## Action Decision Matrix (Guarded)

| Risk Score Range | Decision Action | Description |
|---|---|---|
| **0 - 29** | `ALLOW` | Low risk; transaction proceeds seamlessly. |
| **30 - 69** | `STEP_UP_2FA` | Moderate risk; requires secondary authentication challenge. |
| **70 - 89** | `MANUAL_REVIEW` | High risk; queued for analyst investigation with synthesized evidence. |
| **90 - 100** | `BLOCK` | Critical risk / confirmed fraud pattern; immediate transaction block. |
