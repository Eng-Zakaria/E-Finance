"""
Transaction Analytics Endpoints
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query

from app.spark.analytics import transaction_analytics, risk_analytics

router = APIRouter()


@router.get("/volume")
async def get_transaction_volume(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get transaction volume analytics.
    """
    start = datetime.fromisoformat(start_date) if start_date else datetime.now() - timedelta(days=30)
    end = datetime.fromisoformat(end_date) if end_date else datetime.now()
    
    # Load and analyze
    df = transaction_analytics.load_transactions(start, end)
    volume_df = transaction_analytics.calculate_daily_volume(df)
    
    # Convert to dict for response
    result = volume_df.toPandas().to_dict(orient="records")
    
    return {
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "data": result
    }


@router.get("/summary")
async def get_account_summary():
    """
    Get account-level transaction summary.
    """
    df = transaction_analytics.load_transactions(
        datetime.now() - timedelta(days=90),
        datetime.now()
    )
    summary_df = transaction_analytics.calculate_account_summary(df)
    
    result = summary_df.toPandas().to_dict(orient="records")
    
    return {"accounts": result}


@router.get("/anomalies")
async def get_anomalies():
    """
    Detect anomalous transactions.
    """
    df = transaction_analytics.load_transactions(
        datetime.now() - timedelta(days=30),
        datetime.now()
    )
    anomalies_df = transaction_analytics.detect_anomalies(df)
    
    result = anomalies_df.toPandas().to_dict(orient="records")
    
    return {"anomalies": result, "count": len(result)}


@router.get("/risk-scores")
async def get_risk_scores():
    """
    Get risk scores for accounts.
    """
    df = transaction_analytics.load_transactions(
        datetime.now() - timedelta(days=90),
        datetime.now()
    )
    risk_df = risk_analytics.calculate_risk_scores(df)
    
    result = risk_df.toPandas().to_dict(orient="records")
    
    return {"accounts": result}

