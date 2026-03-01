"""
Wallet Endpoints
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    WalletCreate, WalletResponse, WalletBalance, NetworkType
)
from app.blockchain.wallet_manager import wallet_manager

router = APIRouter()


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_wallet(request: WalletCreate):
    """
    Create a new crypto wallet.
    Returns wallet info and mnemonic (shown only once!).
    """
    wallet, mnemonic = await wallet_manager.create_wallet(
        user_id=request.user_id,
        network=request.network,
        label=request.label
    )
    
    return {
        "wallet": wallet.model_dump(),
        "mnemonic": mnemonic,
        "warning": "Save this mnemonic phrase securely. It will NOT be shown again!"
    }


@router.get("/user/{user_id}", response_model=List[WalletResponse])
async def get_user_wallets(user_id: UUID):
    """
    Get all wallets for a user.
    """
    wallets = await wallet_manager.get_user_wallets(user_id)
    return wallets


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet(wallet_id: UUID):
    """
    Get wallet details.
    """
    wallet = await wallet_manager.get_wallet(wallet_id)
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    return WalletResponse(
        id=wallet["id"],
        user_id=wallet["user_id"],
        address=wallet["address"],
        network=wallet["network"],
        label=wallet["label"],
        is_active=wallet["is_active"],
        created_at=wallet["created_at"]
    )


@router.get("/{wallet_id}/balance", response_model=WalletBalance)
async def get_wallet_balance(wallet_id: UUID, include_tokens: bool = True):
    """
    Get wallet balance including tokens.
    """
    balance = await wallet_manager.get_wallet_balance(wallet_id, include_tokens)
    
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    return balance


@router.post("/import", response_model=WalletResponse)
async def import_wallet(
    user_id: UUID,
    private_key: str,
    network: NetworkType = NetworkType.ETHEREUM,
    label: str = None
):
    """
    Import existing wallet from private key.
    """
    wallet = await wallet_manager.import_wallet(
        user_id=user_id,
        private_key=private_key,
        network=network,
        label=label
    )
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to import wallet"
        )
    
    return wallet


@router.delete("/{wallet_id}", response_model=dict)
async def deactivate_wallet(wallet_id: UUID):
    """
    Deactivate a wallet (soft delete).
    """
    success = await wallet_manager.deactivate_wallet(wallet_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    return {"message": "Wallet deactivated successfully"}

