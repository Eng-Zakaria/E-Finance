"""
Fraud Detection API Routes
"""
from fastapi import APIRouter

from app.api.endpoints import fraud, aml, monitoring

router = APIRouter()

router.include_router(fraud.router, prefix="/fraud", tags=["Fraud Detection"])
router.include_router(aml.router, prefix="/aml", tags=["AML Compliance"])
router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])

