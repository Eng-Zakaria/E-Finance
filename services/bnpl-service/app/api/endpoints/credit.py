"""
Credit Endpoints
"""
from typing import Dict
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Query

from app.models.schemas import (
    CreditCheckRequest, CreditCheckResponse, EligibilityResponse,
    CreditScoreFactors
)
from app.services.credit_scoring import credit_scoring_service
from app.config import settings

router = APIRouter()


@router.post("/check", response_model=CreditCheckResponse)
async def check_credit(request: CreditCheckRequest):
    """
    Check credit eligibility for a user.
    """
    result = await credit_scoring_service.check_eligibility(
        request.user_id,
        request.requested_amount
    )
    return result


@router.get("/score/{user_id}", response_model=CreditScoreFactors)
async def get_credit_score(user_id: UUID):
    """
    Get detailed credit score breakdown for a user.
    """
    score, factors = await credit_scoring_service.calculate_credit_score(user_id)
    return factors


@router.get("/eligibility", response_model=EligibilityResponse)
async def check_eligibility(
    user_id: UUID,
    amount: int = Query(..., gt=0)
):
    """
    Quick eligibility check for a purchase amount.
    """
    result = await credit_scoring_service.check_eligibility(user_id, amount)
    
    # Calculate monthly payment estimates
    estimates = {}
    for installments in settings.INSTALLMENT_OPTIONS:
        estimates[installments] = amount // installments
    
    return EligibilityResponse(
        is_eligible=result.is_approved,
        max_amount=result.available_credit,
        available_installment_options=settings.INSTALLMENT_OPTIONS[:result.max_installments // 3 + 1],
        monthly_payment_estimates=estimates,
        reasons=result.rejection_reasons
    )


@router.get("/limit/{user_id}", response_model=dict)
async def get_credit_limit(user_id: UUID):
    """
    Get credit limit for a user.
    """
    limit = await credit_scoring_service.calculate_credit_limit(user_id)
    
    # Mock used credit for demo
    used = 30000  # $300
    
    return {
        "user_id": str(user_id),
        "credit_limit": limit,
        "used_credit": used,
        "available_credit": limit - used,
        "utilization_percent": round(used / limit * 100, 1) if limit > 0 else 0
    }

