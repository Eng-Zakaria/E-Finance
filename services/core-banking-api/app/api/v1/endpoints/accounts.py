"""
Account Endpoints
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.account_service import AccountService
from app.schemas.account import (
    AccountCreate, AccountResponse, AccountListResponse, AccountBalanceResponse,
    TransferRequest, TransferResponse, DepositRequest, WithdrawalRequest,
    ExternalTransferRequest, AccountUpdateRequest
)
from app.api.v1.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    data: AccountCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new bank account.
    """
    account_service = AccountService(session)
    account, error = await account_service.create_account(current_user.id, data)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return AccountResponse.model_validate(account)


@router.get("/", response_model=AccountListResponse)
async def list_accounts(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all accounts for current user.
    """
    account_service = AccountService(session)
    return await account_service.get_user_accounts(current_user.id)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get account details.
    """
    account_service = AccountService(session)
    account = await account_service.get_account(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    if account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    return AccountResponse.model_validate(account)


@router.get("/{account_id}/balance", response_model=AccountBalanceResponse)
async def get_account_balance(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get account balance.
    """
    account_service = AccountService(session)
    account = await account_service.get_account(account_id)
    
    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    balance = await account_service.get_balance(account_id)
    return balance


@router.post("/{account_id}/deposit", response_model=TransferResponse)
async def deposit(
    account_id: UUID,
    data: DepositRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Deposit funds into account.
    """
    account_service = AccountService(session)
    account = await account_service.get_account(account_id)
    
    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    response, error = await account_service.deposit(account_id, data)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return response


@router.post("/{account_id}/withdraw", response_model=TransferResponse)
async def withdraw(
    account_id: UUID,
    data: WithdrawalRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Withdraw funds from account.
    """
    account_service = AccountService(session)
    account = await account_service.get_account(account_id)
    
    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    response, error = await account_service.withdraw(account_id, data)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return response


@router.post("/transfer", response_model=TransferResponse)
async def internal_transfer(
    data: TransferRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Transfer funds between internal accounts.
    """
    account_service = AccountService(session)
    response, error = await account_service.internal_transfer(current_user.id, data)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return response


@router.post("/transfer/external", response_model=TransferResponse)
async def external_transfer(
    data: ExternalTransferRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Transfer funds to external bank account.
    """
    account_service = AccountService(session)
    response, error = await account_service.external_transfer(current_user.id, data)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return response


@router.delete("/{account_id}", response_model=dict)
async def close_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Close an account.
    """
    account_service = AccountService(session)
    success, error = await account_service.close_account(account_id, current_user.id)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"message": "Account closed successfully"}

