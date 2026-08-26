# RISK-X Backend Service

FastAPI-powered asynchronous backend service for RISK-X payment risk investigation.

---

## Directory Structure

```
backend/
├── app/
│   ├── api/            # API routes and controllers (to be added incrementally)
│   ├── core/           # Configuration settings and environment variables
│   │   ├── __init__.py
│   │   └── config.py
│   ├── __init__.py
│   └── main.py         # Application entrypoint with /health endpoint
├── requirements.txt    # Python dependencies
└── README.md
```

---

## Setup & Running

### 1. Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Backend Server
```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Verify Endpoints
- **Health Check**: `GET http://localhost:8000/health`
  ```json
  {
    "status": "healthy",
    "service": "RISK-X",
    "version": "0.1.0",
    "message": "RISK-X backend is running and operational"
  }
  ```
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Running Tests
From the root directory:
```bash
pytest tests/backend/
```
