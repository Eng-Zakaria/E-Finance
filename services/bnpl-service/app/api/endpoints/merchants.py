"""
Merchant Endpoints
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from app.models.schemas import MerchantResponse
from app.services.order_service import order_service

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_merchants():
    """
    List all active merchants.
    """
    merchants = await order_service.get_merchants()
    return merchants


@router.get("/{merchant_id}", response_model=dict)
async def get_merchant(merchant_id: UUID):
    """
    Get merchant details.
    """
    merchant = await order_service.get_merchant(merchant_id)
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    return merchant


@router.get("/categories", response_model=List[str])
async def list_categories():
    """
    List available merchant categories.
    """
    return [
        "electronics",
        "fashion",
        "home",
        "beauty",
        "sports",
        "travel",
        "education",
        "healthcare"
    ]

