"""
Fraud Detection Endpoints
"""
from typing import List
from datetime import datetime
from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    TransactionAnalysisRequest, FraudScore, FraudAlert,
    BatchAnalysisRequest, BatchAnalysisResponse
)
from app.ml.fraud_detector import fraud_detector

router = APIRouter()


@router.post("/analyze", response_model=FraudScore)
async def analyze_transaction(request: TransactionAnalysisRequest):
    """
    Analyze a single transaction for fraud.
    Returns risk score and recommendations.
    """
    try:
        score = await fraud_detector.analyze_transaction(request)
        return score
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/analyze/batch", response_model=BatchAnalysisResponse)
async def batch_analyze_transactions(request: BatchAnalysisRequest):
    """
    Analyze multiple transactions in batch.
    """
    start_time = datetime.utcnow()
    
    try:
        results = await fraud_detector.batch_analyze(request.transactions)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        suspicious_count = sum(1 for r in results if r.is_suspicious)
        
        return BatchAnalysisResponse(
            total_analyzed=len(results),
            suspicious_count=suspicious_count,
            results=results,
            processing_time_ms=processing_time
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch analysis failed: {str(e)}"
        )


@router.post("/alert", response_model=FraudAlert)
async def create_fraud_alert(
    transaction: TransactionAnalysisRequest,
    fraud_score: FraudScore
):
    """
    Create a fraud alert for a suspicious transaction.
    """
    alert = await fraud_detector.create_alert(transaction, fraud_score)
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction does not require an alert"
        )
    
    return alert


@router.get("/rules", response_model=List[dict])
async def get_fraud_rules():
    """
    Get current fraud detection rules.
    """
    rules = []
    for rule in fraud_detector.rules:
        rules.append({
            "id": rule["id"],
            "name": rule["name"],
            "score_impact": rule["score_impact"],
            "alert_type": rule["alert_type"].value
        })
    return rules


@router.get("/thresholds", response_model=dict)
async def get_thresholds():
    """
    Get current fraud detection thresholds.
    """
    from app.config import settings
    
    return {
        "fraud_score_threshold": settings.FRAUD_SCORE_THRESHOLD,
        "high_risk_threshold": settings.HIGH_RISK_THRESHOLD,
        "critical_risk_threshold": settings.CRITICAL_RISK_THRESHOLD,
        "large_transaction_threshold": settings.LARGE_TRANSACTION_THRESHOLD,
        "max_daily_transactions": settings.MAX_DAILY_TRANSACTIONS,
        "max_daily_amount": settings.MAX_DAILY_AMOUNT
    }

