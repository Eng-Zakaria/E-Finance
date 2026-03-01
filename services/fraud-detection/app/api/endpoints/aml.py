"""
AML (Anti-Money Laundering) Endpoints
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Query

from app.models.schemas import AMLCheckRequest, AMLCheckResult
from app.ml.aml_checker import aml_checker

router = APIRouter()


@router.post("/check", response_model=AMLCheckResult)
async def perform_aml_check(request: AMLCheckRequest):
    """
    Perform comprehensive AML check on a user.
    Includes sanctions screening, PEP check, and adverse media.
    """
    try:
        result = await aml_checker.check(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AML check failed: {str(e)}"
        )


@router.post("/transaction-check", response_model=dict)
async def check_transaction_aml(
    user_id: UUID,
    transaction_amount: int = Query(..., gt=0),
    counterparty_name: Optional[str] = None,
    counterparty_country: Optional[str] = None
):
    """
    Quick AML check for a transaction.
    """
    try:
        result = await aml_checker.check_transaction(
            user_id,
            transaction_amount,
            counterparty_name,
            counterparty_country
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction AML check failed: {str(e)}"
        )


@router.get("/high-risk-countries", response_model=list)
async def get_high_risk_countries():
    """
    Get list of high-risk countries for AML purposes.
    """
    return list(aml_checker.HIGH_RISK_COUNTRIES)


@router.get("/reporting-threshold", response_model=dict)
async def get_reporting_threshold():
    """
    Get transaction amount threshold for mandatory reporting.
    """
    from app.config import settings
    
    return {
        "threshold_cents": settings.LARGE_TRANSACTION_THRESHOLD,
        "threshold_dollars": settings.LARGE_TRANSACTION_THRESHOLD / 100,
        "structuring_threshold_cents": settings.STRUCTURING_THRESHOLD,
        "description": "Transactions above this threshold require enhanced due diligence and may trigger reporting requirements."
    }

