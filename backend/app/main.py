"""RISK-X Backend Main Application Entrypoint."""

import sys
from pathlib import Path

# Ensure repository root is on sys.path for ML package artifact deserialization
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_v1_router
from app.engine.service import risk_service

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup CORS middleware for local frontend and production deployment communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 routes
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    """Root endpoint returning service identity and navigation links."""
    return {
        "service": settings.PROJECT_NAME,
        "description": settings.PROJECT_DESCRIPTION,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
        "readiness": "/health/ready",
        "api_v1": settings.API_V1_STR,
    }


@app.get("/health")
def health_liveness():
    """Liveness probe: verifies that the FastAPI application process is running."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "message": "RISK-X backend process is operational",
    }


@app.get("/health/ready")
@app.get("/ready")
def health_readiness():
    """Readiness probe: verifies that ML models and preprocessor artifacts are accessible and loaded."""
    readiness = risk_service.check_readiness()
    if not readiness["ready"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unready",
                "message": "Model artifacts unavailable or failing to load",
                "details": readiness,
            },
        )
    return {
        "status": "ready",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "model_loaded": readiness["model_loaded"],
        "preprocessor_loaded": readiness["preprocessor_loaded"],
    }
