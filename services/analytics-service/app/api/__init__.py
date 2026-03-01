"""
Analytics API Routes
"""
from fastapi import APIRouter

from app.api.endpoints import transactions, reports

router = APIRouter()

router.include_router(transactions.router, prefix="/transactions", tags=["Transaction Analytics"])
router.include_router(reports.router, prefix="/reports", tags=["Reports"])

