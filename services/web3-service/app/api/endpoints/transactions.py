"""
Crypto Transaction Endpoints
"""
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    CryptoTransferRequest, CryptoTransferResponse, TransactionStatus, NetworkType
)
from app.blockchain.wallet_manager import wallet_manager
from app.blockchain.ethereum import ethereum_client

router = APIRouter()


@router.post("/transfer", response_model=CryptoTransferResponse)
async def transfer_crypto(request: CryptoTransferRequest):
    """
    Send cryptocurrency to another address.
    """
    # Get wallet
    wallet = await wallet_manager.get_wallet(request.from_wallet_id)
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    if not wallet["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wallet is not active"
        )
    
    # Get private key
    private_key = await wallet_manager.get_private_key(request.from_wallet_id)
    
    # Send transaction
    if request.token_address:
        # ERC-20 token transfer
        tx_hash = await ethereum_client.send_token_transaction(
            token_address=request.token_address,
            from_address=wallet["address"],
            to_address=request.to_address,
            amount=int(request.amount),
            private_key=private_key,
            gas_limit=request.gas_limit,
            gas_price_gwei=request.gas_price_gwei
        )
    else:
        # Native token transfer
        tx_hash = await ethereum_client.send_transaction(
            from_address=wallet["address"],
            to_address=request.to_address,
            value=int(request.amount),
            private_key=private_key,
            gas_limit=request.gas_limit,
            gas_price_gwei=request.gas_price_gwei
        )
    
    if not tx_hash:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transaction failed"
        )
    
    # Format amount
    if request.network == NetworkType.ETHEREUM:
        decimals = 18
        symbol = "ETH"
    else:
        decimals = 18
        symbol = "TOKEN"
    
    amount_formatted = f"{int(request.amount) / 10**decimals:.6f} {symbol}"
    
    return CryptoTransferResponse(
        transaction_id=uuid4(),
        tx_hash=tx_hash,
        from_address=wallet["address"],
        to_address=request.to_address,
        amount=request.amount,
        amount_formatted=amount_formatted,
        network=request.network,
        token_address=request.token_address,
        status=TransactionStatus.PENDING,
        created_at=datetime.utcnow()
    )


@router.get("/{tx_hash}/status", response_model=dict)
async def get_transaction_status(tx_hash: str):
    """
    Get transaction status by hash.
    """
    receipt = ethereum_client.get_transaction_receipt(tx_hash)
    
    if not receipt:
        return {
            "tx_hash": tx_hash,
            "status": TransactionStatus.PENDING.value,
            "message": "Transaction is pending or not found"
        }
    
    status = TransactionStatus.CONFIRMED if receipt.get("status") == 1 else TransactionStatus.FAILED
    
    return {
        "tx_hash": tx_hash,
        "status": status.value,
        "block_number": receipt.get("blockNumber"),
        "gas_used": receipt.get("gasUsed"),
        "confirmations": 1  # Would calculate actual confirmations in production
    }


@router.get("/history/{wallet_id}", response_model=list)
async def get_transaction_history(
    wallet_id: UUID,
    limit: int = 50,
    offset: int = 0
):
    """
    Get transaction history for a wallet.
    """
    wallet = await wallet_manager.get_wallet(wallet_id)
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    # In production, would query from database or blockchain explorer API
    # For now, return empty list
    return []

