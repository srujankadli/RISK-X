"""API v1 Router Registration."""

from fastapi import APIRouter
from app.api.v1.risk import router as risk_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.transactions import router as transactions_router

api_v1_router = APIRouter()
api_v1_router.include_router(risk_router)
api_v1_router.include_router(webhooks_router)
api_v1_router.include_router(transactions_router)

__all__ = ["api_v1_router"]
