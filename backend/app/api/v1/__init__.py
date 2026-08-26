"""API v1 Router Registration."""

from fastapi import APIRouter
from app.api.v1.risk import router as risk_router

api_v1_router = APIRouter()
api_v1_router.include_router(risk_router)

__all__ = ["api_v1_router"]
