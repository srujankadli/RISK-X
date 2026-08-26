"""Transaction Ledger and History Router for RISK-X."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.db.repository import get_transaction_repository
from app.schemas.webhook import (
    RiskStatsResponse,
    TransactionHistoryItem,
    TransactionHistoryResponse,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get(
    "",
    response_model=TransactionHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="List historical transaction assessments",
    description="Retrieve paginated list of assessed transactions with optional filters for decision, risk level, or text search.",
)
async def list_transactions(
    limit: int = Query(50, ge=1, le=100, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    decision: Optional[str] = Query(None, description="Filter by decision: ALLOW, REVIEW, BLOCK"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level: LOW, MEDIUM, HIGH"),
    search: Optional[str] = Query(None, description="Search query for transaction ID, customer ID, or merchant ID"),
) -> TransactionHistoryResponse:
    """Retrieve filtered and paginated list of transaction records."""
    repo = get_transaction_repository()
    items, total = repo.list_transactions(
        limit=limit,
        offset=offset,
        decision=decision,
        risk_level=risk_level,
        search=search,
    )
    return TransactionHistoryResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/stats",
    response_model=RiskStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve aggregate risk statistics",
    description="Get real-time summary statistics across all processed transactions (total, decision breakdown, average risk score).",
)
async def get_risk_statistics() -> RiskStatsResponse:
    """Retrieve aggregate transaction metrics for dashboard cards."""
    repo = get_transaction_repository()
    stats = repo.get_risk_stats()
    return RiskStatsResponse(**stats)


@router.get(
    "/{transaction_id}",
    response_model=TransactionHistoryItem,
    status_code=status.HTTP_200_OK,
    summary="Retrieve specific transaction assessment record",
    description="Fetch full audit record, including all input features, decision, evidence array, reasons, and timestamps by ID.",
)
async def get_transaction(transaction_id: str) -> TransactionHistoryItem:
    """Fetch complete transaction details by unique transaction_id."""
    repo = get_transaction_repository()
    record = repo.get_transaction_by_id(transaction_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID '{transaction_id}' not found in ledger.",
        )
    return TransactionHistoryItem(**record)
