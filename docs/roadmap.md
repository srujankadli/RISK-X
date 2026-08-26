# RISK-X Project Roadmap & Milestones

Target Completion: September 5, 2026

---

## Milestone Breakdown

### Milestone 1: Project Foundation (Completed)
- [x] Establish modular repository structure (`backend/`, `frontend/`, `ml/`, `data/`, `investigations/`, `tests/`, `docs/`)
- [x] Configure FastAPI backend environment and `/health` endpoint
- [x] Configure React + Vite frontend environment
- [x] Set up `.gitignore`, root documentation, and architectural plans
- [x] Verify backend and frontend initialization

### Milestone 2: Data Modeling & Synthetic Data Pipeline
- [ ] Implement Razorpay transaction data schema with Pydantic
- [ ] Build synthetic dataset generator simulating legitimate payments and known fraud patterns:
  - Velocity bursts (card testing)
  - Geolocation jumps (impossible travel)
  - Amount anomalies (unusually high single transactions)
  - Device/IP rotation attacks
- [ ] Save processed baseline datasets in `data/processed/`

### Milestone 3: Fast Rules & Machine Learning Scoring
- [ ] Implement deterministic rule engine with configurable rule set
- [ ] Train baseline `scikit-learn` anomaly / classification model
- [ ] Implement composite risk scoring combining rules + ML score (0-100 scale)
- [ ] Unit test scoring pipeline accuracy and latency

### Milestone 4: Investigation Engine & Guarded Decisions
- [ ] Build investigation case generator
- [ ] Assemble structured Evidence Packages (JSON) with reason codes
- [ ] Implement deterministic decision matrix (ALLOW, STEP_UP_2FA, MANUAL_REVIEW, BLOCK)
- [ ] Persist cases and audit trail into SQLite database

### Milestone 5: Analyst Frontend Dashboard
- [ ] Build live transaction monitoring feed in React
- [ ] Build Case Detail view with interactive Evidence Breakdown
- [ ] Implement manual review triage controls and resolution workflow
- [ ] Add summary charts (risk score distribution, action breakdown) using Recharts

### Milestone 6: AI-Powered Evidence Synthesis & Final Hardening
- [ ] Integrate LLM agent for natural-language case summary and investigation rationale
- [ ] Ensure strict boundaries between AI explanations and deterministic action execution
- [ ] End-to-end integration and load testing
- [ ] Finalize buildathon demo and documentation
