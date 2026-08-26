# RISK-X Analyst Dashboard

React + Vite frontend for the **RISK-X (Risk Investigation System X)** real-time payment risk assessment and decisioning platform.

---

## Features

- **Real-Time Transaction Assessment Console**: Interactive form for all 13 observable payment and behavioral parameters.
- **One-Click Scenario Presets**: Instant simulation of *Normal Transactions*, *Suspicious Velocity*, and *High-Risk Attack Clusters*.
- **Decision & Risk Score Cockpit**: High-visibility metric cards displaying 0–100 deterministic risk scores, Random Forest predicted fraud probabilities, and policy badges (`ALLOW` / `REVIEW` / `BLOCK`).
- **Ranked Structured Evidence Matrix**: Severity-ordered (`HIGH` / `MEDIUM` / `LOW`) evidence signals detailing observed values vs reference thresholds.
- **Analyst Narrative Summary**: Backend-synthesized contextual summary explaining primary risk drivers.
- **Engine Readiness & Liveness Tracking**: Continuous health polling against `/health/ready` verifying backend and model artifact availability.
- **Raw JSON Inspector**: Expandable inspection viewer for audit tracing.

---

## Directory Structure

```
frontend/
├── src/
│   ├── App.jsx         # Analyst Dashboard component with real API integration
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

## API Integration

The dashboard integrates directly with the live FastAPI backend:
- `GET http://localhost:8000/health/ready`: Readiness probe verifying ML model and preprocessor status.
- `POST http://localhost:8000/api/v1/risk/assess`: Real-time transaction risk scoring, policy evaluation, and evidence extraction.

---

## Demonstration Workflow

1. Open `http://localhost:5173` in your browser.
2. Verify the top right status reads **`ML Detector Online`**.
3. Click the **`🟢 Normal Transaction`** preset and click **`Run Real-Time Risk Assessment`** $\rightarrow$ Observe **`ALLOW`** decision with a low risk score and no elevated signals.
4. Click the **`🟡 Suspicious Activity`** preset and submit $\rightarrow$ Observe **`REVIEW`** decision with moderate velocity/retry signals.
5. Click the **`🔴 High-Risk Attack Cluster`** preset and submit $\rightarrow$ Observe **`BLOCK`** decision with high risk score, multiple `HIGH` severity signals (amount anomaly, device multi-account reuse, velocity burst), and full analyst narrative.
