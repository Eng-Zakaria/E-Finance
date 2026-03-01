"""
Report Generation Endpoints
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Query

from app.spark.analytics import customer_analytics, transaction_analytics

router = APIRouter()


@router.get("/customer-segments")
async def get_customer_segments():
    """
    Get customer segmentation analysis.
    """
    df = transaction_analytics.load_transactions(
        datetime.now() - timedelta(days=90),
        datetime.now()
    )
    segments_df = customer_analytics.segment_customers(df)
    
    result = segments_df.toPandas().to_dict(orient="records")
    
    # Summary by segment
    segment_summary = segments_df.groupBy("segment").count().toPandas().to_dict(orient="records")
    
    return {
        "segments": result,
        "summary": segment_summary
    }


@router.get("/monthly-statement/{account_id}")
async def get_monthly_statement(
    account_id: str,
    year: int = Query(default=2024),
    month: int = Query(default=1, ge=1, le=12)
):
    """
    Generate monthly statement for account.
    """
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # Mock statement data
    return {
        "account_id": account_id,
        "period": {
            "year": year,
            "month": month,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "opening_balance": 100000,
        "closing_balance": 125000,
        "total_credits": 50000,
        "total_debits": 25000,
        "transaction_count": 15
    }


@router.get("/financial-summary")
async def get_financial_summary(
    period: str = Query(default="monthly", pattern="^(daily|weekly|monthly|yearly)$")
):
    """
    Get overall financial summary.
    """
    return {
        "period": period,
        "total_users": 10000,
        "total_accounts": 15000,
        "total_transaction_volume": 5000000000,  # $50M
        "total_transactions": 150000,
        "avg_transaction_value": 33333,
        "active_bnpl_orders": 2500,
        "crypto_wallet_balance": 1000000000,  # $10M equivalent
        "fraud_alerts": 150,
        "fraud_blocked_amount": 500000
    }

