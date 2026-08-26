"""
RISK-X Risk Assessment API Endpoints
====================================
FastAPI router for real-time transaction scoring, risk decisioning, and service readiness.
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.risk import TransactionAssessmentRequest, RiskAssessmentResponse
from app.engine.service import risk_service

router = APIRouter(prefix="/risk", tags=["Risk Assessment"])


@router.post(
    "/assess",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Assess transaction risk score, decision, and reasons",
    description=(
        "Evaluates an incoming payment transaction through the RISK-X Random Forest detector, "
        "calculates a deterministic 0-100 risk score, applies deterministic policy thresholds "
        "(ALLOW / REVIEW / BLOCK), and returns explainable risk signals."
    ),
)
def assess_transaction(payload: TransactionAssessmentRequest) -> RiskAssessmentResponse:
    """Assess risk for a single payment transaction in real time."""
    try:
        response = risk_service.assess_transaction(payload)
        return response
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model artifacts unavailable: {str(e)}",
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model artifact loading failure: {str(e)}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transaction evaluation parameters: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk assessment failure: {str(e)}",
        )


@router.get(
    "/readiness",
    status_code=status.HTTP_200_OK,
    summary="Check ML risk engine readiness",
    description="Verifies that ML model and preprocessor artifacts are accessible and loaded into memory.",
)
def risk_readiness():
    """Readiness probe for the ML risk engine."""
    readiness = risk_service.check_readiness()
    if not readiness["ready"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=readiness,
        )
    return readiness
