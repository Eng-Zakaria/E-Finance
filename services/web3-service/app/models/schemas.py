"""
Web3 Service Schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum
from decimal import Decimal


class NetworkType(str, Enum):
    """Blockchain network types"""
    ETHEREUM = "ethereum"
    BSC = "bsc"
    POLYGON = "polygon"
    BITCOIN = "bitcoin"


class TokenType(str, Enum):
    """Token types"""
    NATIVE = "native"  # ETH, BNB, MATIC
    ERC20 = "erc20"
    ERC721 = "erc721"
    ERC1155 = "erc1155"
    BEP20 = "bep20"


class TransactionStatus(str, Enum):
    """Blockchain transaction status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    DROPPED = "dropped"


class WalletCreate(BaseModel):
    """Create wallet request"""
    user_id: UUID
    network: NetworkType = NetworkType.ETHEREUM
    label: Optional[str] = None


class WalletResponse(BaseModel):
    """Wallet response"""
    id: UUID
    user_id: UUID
    address: str
    network: NetworkType
    label: Optional[str] = None
    is_active: bool = True
    created_at: datetime


class WalletBalance(BaseModel):
    """Wallet balance"""
    wallet_id: UUID
    address: str
    network: NetworkType
    native_balance: str  # In wei/satoshi
    native_balance_formatted: str  # Human readable
    native_symbol: str
    tokens: List[Dict[str, Any]] = []
    last_updated: datetime


class TokenBalance(BaseModel):
    """Token balance"""
    contract_address: str
    symbol: str
    name: str
    decimals: int
    balance: str
    balance_formatted: str
    token_type: TokenType


class CryptoTransferRequest(BaseModel):
    """Crypto transfer request"""
    from_wallet_id: UUID
    to_address: str
    amount: str = Field(..., description="Amount in smallest unit (wei/satoshi)")
    network: NetworkType
    token_address: Optional[str] = None  # None for native token
    gas_price_gwei: Optional[int] = None
    gas_limit: Optional[int] = None


class CryptoTransferResponse(BaseModel):
    """Crypto transfer response"""
    transaction_id: UUID
    tx_hash: str
    from_address: str
    to_address: str
    amount: str
    amount_formatted: str
    network: NetworkType
    token_address: Optional[str] = None
    gas_used: Optional[int] = None
    gas_price: Optional[str] = None
    fee: Optional[str] = None
    status: TransactionStatus
    block_number: Optional[int] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None


class SwapRequest(BaseModel):
    """Token swap request"""
    wallet_id: UUID
    from_token: str  # Token address or 'ETH'
    to_token: str
    amount: str
    slippage_percent: float = Field(default=0.5, ge=0.1, le=5.0)
    network: NetworkType = NetworkType.ETHEREUM


class SwapQuote(BaseModel):
    """Swap quote response"""
    from_token: str
    from_token_symbol: str
    to_token: str
    to_token_symbol: str
    amount_in: str
    amount_out: str
    price_impact: float
    route: List[str]
    gas_estimate: int
    valid_until: datetime


class SwapResponse(BaseModel):
    """Swap execution response"""
    transaction_id: UUID
    tx_hash: str
    from_token: str
    to_token: str
    amount_in: str
    amount_out: str
    status: TransactionStatus
    created_at: datetime


class StakeRequest(BaseModel):
    """Staking request"""
    wallet_id: UUID
    protocol: str  # e.g., 'lido', 'rocketpool'
    amount: str
    network: NetworkType = NetworkType.ETHEREUM


class StakeResponse(BaseModel):
    """Staking response"""
    transaction_id: UUID
    tx_hash: str
    protocol: str
    staked_amount: str
    received_token: str
    received_amount: str
    apy: float
    status: TransactionStatus
    created_at: datetime


class LendRequest(BaseModel):
    """DeFi lending request"""
    wallet_id: UUID
    protocol: str  # e.g., 'aave', 'compound'
    token_address: str
    amount: str
    network: NetworkType = NetworkType.ETHEREUM


class LendResponse(BaseModel):
    """DeFi lending response"""
    transaction_id: UUID
    tx_hash: str
    protocol: str
    deposited_amount: str
    atoken_received: str
    current_apy: float
    status: TransactionStatus
    created_at: datetime


class BorrowRequest(BaseModel):
    """DeFi borrow request"""
    wallet_id: UUID
    protocol: str
    token_address: str
    amount: str
    collateral_token: str
    collateral_amount: str
    network: NetworkType = NetworkType.ETHEREUM


class NFTResponse(BaseModel):
    """NFT token response"""
    contract_address: str
    token_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    metadata_url: Optional[str] = None
    token_type: TokenType
    owner: str


class GasPrice(BaseModel):
    """Current gas prices"""
    network: NetworkType
    slow: int  # Gwei
    standard: int
    fast: int
    instant: int
    base_fee: Optional[int] = None
    last_updated: datetime


class TransactionHistory(BaseModel):
    """Transaction history item"""
    tx_hash: str
    block_number: int
    timestamp: datetime
    from_address: str
    to_address: str
    value: str
    token_address: Optional[str] = None
    token_symbol: Optional[str] = None
    status: TransactionStatus
    gas_used: int
    gas_price: str
    fee: str
    transaction_type: str  # send, receive, swap, stake, etc.

