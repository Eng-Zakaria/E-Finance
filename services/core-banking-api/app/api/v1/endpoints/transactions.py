"""
Transaction Endpoints
"""
from typing import Optional
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.transaction_service import TransactionService
from app.schemas.transaction import (
    TransactionResponse, TransactionListResponse, TransactionFilterParams,
    TransactionAnalytics, DisputeRequest, DisputeResponse
)
from app.api.v1.deps import get_current_user, get_current_admin
from app.models.user import User
from app.models.transaction import TransactionType, TransactionStatus, RiskLevel

router = APIRouter()


@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    account_id: Optional[UUID] = None,
    transaction_type: Optional[TransactionType] = None,
    status_filter: Optional[TransactionStatus] = None,
    min_amount: Optional[int] = None,
    max_amount: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get paginated list of transactions with filters.
    """
    transaction_service = TransactionService(session)
    
    filters = TransactionFilterParams(
        account_id=account_id,
        transaction_type=transaction_type,
        status=status_filter,
        min_amount=min_amount,
        max_amount=max_amount,
        start_date=start_date,
        end_date=end_date
    )
    
    return await transaction_service.get_transactions(
        current_user.id,
        filters,
        page,
        page_size
    )


@router.get("/recent", response_model=list[TransactionResponse])
async def get_recent_transactions(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get recent transaction activity.
    """
    transaction_service = TransactionService(session)
    transactions = await transaction_service.get_recent_activity(current_user.id, limit)
    return [TransactionResponse.model_validate(t) for t in transactions]


@router.get("/analytics", response_model=TransactionAnalytics)
async def get_transaction_analytics(
    start_date: datetime,
    end_date: datetime,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get transaction analytics and summaries.
    """
    transaction_service = TransactionService(session)
    return await transaction_service.get_analytics(
        current_user.id,
        start_date,
        end_date
    )


@router.get("/search", response_model=list[TransactionResponse])
async def search_transactions(
    query: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Search transactions by reference, description, or counterparty.
    """
    transaction_service = TransactionService(session)
    transactions = await transaction_service.search_transactions(
        current_user.id,
        query,
        limit
    )
    return [TransactionResponse.model_validate(t) for t in transactions]


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get transaction details.
    """
    transaction_service = TransactionService(session)
    transaction = await transaction_service.get_transaction(transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Verify ownership through account
    from app.services.account_service import AccountService
    account_service = AccountService(session)
    account = await account_service.get_account(transaction.account_id)
    
    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    return TransactionResponse.model_validate(transaction)


@router.post("/{transaction_id}/dispute", response_model=DisputeResponse)
async def create_dispute(
    transaction_id: UUID,
    data: DisputeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a dispute for a transaction.
    """
    data.transaction_id = transaction_id
    transaction_service = TransactionService(session)
    response, error = await transaction_service.create_dispute(current_user.id, data)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return response


# Admin endpoints
@router.get("/admin/flagged", response_model=TransactionListResponse)
async def get_flagged_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Get flagged/suspicious transactions (admin only).
    """
    transaction_service = TransactionService(session)
    return await transaction_service.get_flagged_transactions(page, page_size)


@router.post("/admin/{transaction_id}/review", response_model=dict)
async def review_transaction(
    transaction_id: UUID,
    action: str = Query(..., pattern="^(approve|reject|escalate)$"),
    notes: str = Query(..., min_length=10),
    admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Review and take action on flagged transaction (admin only).
    """
    transaction_service = TransactionService(session)
    success, error = await transaction_service.review_transaction(
        transaction_id,
        action,
        admin.id,
        notes
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"message": f"Transaction {action}d successfully"}

