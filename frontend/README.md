# RISK-X Analyst Dashboard

React + Vite frontend for the **RISK-X (Risk Investigation System X)** real-time payment risk assessment, transaction ledger, and webhook intelligence platform.

---

## Features

- **Real-Time Transaction Assessment Console**: Interactive form for all 13 observable payment and behavioral parameters.
- **One-Click Scenario Presets**: Instant simulation of *Normal Transactions*, *Suspicious Velocity*, and *High-Risk Attack Clusters*.
- **Decision & Risk Score Cockpit**: High-visibility metric cards displaying 0–100 deterministic risk scores, Random Forest predicted fraud probabilities, and policy badges (`ALLOW` / `REVIEW` / `BLOCK`).
- **Ranked Structured Evidence Matrix**: Severity-ordered (`HIGH` / `MEDIUM` / `LOW`) evidence signals detailing observed values vs reference thresholds.
- **Live Transaction Audit Ledger**: Data table showing historical transactions, pagination, filter by decision, and click-to-inspect audit drilldown.
- **Razorpay Webhook Simulator**: Browser-based test tool generating HMAC-SHA256 signatures for live webhook ingestion testing.
- **Live KPI Stats Ribbon**: Real-time aggregation of processed volume, allow rate, review rate, block rate, and average score.
- **Engine Readiness & Liveness Tracking**: Continuous health polling against `/health/ready`.
- **Raw JSON Inspector**: Expandable inspection viewer for audit tracing.

---

## Directory Structure

```
frontend/
├── src/
│   ├── App.jsx         # Analyst Dashboard with Console, Audit Ledger, & Webhook tabs
│   ├── index.css       # Fintech dark/slate theme stylesheet
│   └── main.jsx        # React DOM render entrypoint
├── index.html          # HTML template
├── package.json        # Dependencies and build scripts
├── vite.config.js      # Vite configuration
└── README.md
```

---

## Getting Started

### 1. Start the RISK-X Backend First
From the repository root:
```powershell
.\backend\venv\Scripts\Activate.ps1
uvicorn app.main:app --port 8000 --reload
```

### 2. Install Frontend Dependencies
```bash
cd frontend
npm install
```

### 3. Start Vite Development Server
```bash
npm run dev
```
The dashboard will run on `http://localhost:5173`.

### 4. Build for Production
```bash
npm run build
```
Production assets are generated in `frontend/dist/`.

---

## Demonstration Workflow

1. Open `http://localhost:5173` in your browser.
2. Verify the top right status reads **`ML Detector Online`**.
3. **Assessment Console Tab**: Click **`🟢 Normal Transaction`** $\rightarrow$ **`Run Real-Time Risk Assessment`** $\rightarrow$ Observe **`ALLOW`** decision.
4. **Audit Ledger Tab**: View the recorded transaction in the historical stream. Filter by `ALLOW`, `REVIEW`, or `BLOCK`, and click **`Inspect →`** to load the audit package into the Cockpit.
5. **Razorpay Webhooks Tab**: Send a signed webhook event to `/api/v1/webhooks/razorpay` $\rightarrow$ Observe live HMAC-SHA256 signature verification and automated risk decision.
