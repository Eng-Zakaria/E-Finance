"""
BNPL Service API Routes
"""
from fastapi import APIRouter

from app.api.endpoints import credit, orders, merchants

router = APIRouter()

router.include_router(credit.router, prefix="/credit", tags=["Credit"])
router.include_router(orders.router, prefix="/orders", tags=["Orders"])
router.include_router(merchants.router, prefix="/merchants", tags=["Merchants"])

