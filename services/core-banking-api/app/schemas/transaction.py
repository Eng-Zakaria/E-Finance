"""
Transaction Schemas
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from uuid import UUID

from app.models.transaction import TransactionType, TransactionStatus, TransactionChannel, RiskLevel


class TransactionResponse(BaseModel):
    """Transaction response"""
    id: UUID
    account_id: UUID
    reference_number: str
    transaction_type: TransactionType
    channel: TransactionChannel
    amount: int
    currency: str
    fee: int
    balance_before: int
    balance_after: int
    status: TransactionStatus
    
    # Counterparty
    counterparty_name: Optional[str] = None
    counterparty_bank: Optional[str] = None
    counterparty_account: Optional[str] = None
    
    # Crypto
    blockchain_tx_hash: Optional[str] = None
    blockchain_network: Optional[str] = None
    
    description: Optional[str] = None
    memo: Optional[str] = None
    
    # Risk assessment
    risk_level: RiskLevel
    risk_score: int
    is_suspicious: bool
    
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """List of transactions"""
    transactions: List[TransactionResponse]
    total: int
    page: int
    page_size: int


class TransactionFilterParams(BaseModel):
    """Transaction filter parameters"""
    account_id: Optional[UUID] = None
    transaction_type: Optional[TransactionType] = None
    status: Optional[TransactionStatus] = None
    min_amount: Optional[int] = None
    max_amount: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    risk_level: Optional[RiskLevel] = None


class TransactionSearchRequest(BaseModel):
    """Search transactions"""
    query: str = Field(..., min_length=1)
    account_id: Optional[UUID] = None
    limit: int = Field(default=50, le=100)


class TransactionAnalytics(BaseModel):
    """Transaction analytics"""
    total_transactions: int
    total_credits: int
    total_debits: int
    net_flow: int
    average_transaction_amount: float
    largest_transaction: int
    transaction_by_type: dict[str, int]
    transaction_by_status: dict[str, int]
    daily_volume: List[dict[str, Any]]


class FraudAlertResponse(BaseModel):
    """Fraud alert response"""
    id: UUID
    transaction_id: UUID
    alert_type: str
    severity: str
    description: str
    flags: List[str]
    risk_score: int
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[UUID] = None
    resolution: Optional[str] = None


class TransactionReviewRequest(BaseModel):
    """Review flagged transaction"""
    transaction_id: UUID
    action: str = Field(..., pattern="^(approve|reject|escalate)$")
    notes: str = Field(..., min_length=10)


class DisputeRequest(BaseModel):
    """Transaction dispute request"""
    transaction_id: UUID
    reason: str = Field(..., pattern="^(unauthorized|duplicate|incorrect_amount|not_received|other)$")
    description: str = Field(..., min_length=20)
    supporting_documents: Optional[List[str]] = None


class DisputeResponse(BaseModel):
    """Dispute response"""
    id: UUID
    transaction_id: UUID
    status: str
    reason: str
    description: str
    estimated_resolution_date: datetime
    created_at: datetime


class RecurringTransactionCreate(BaseModel):
    """Create recurring transaction"""
    from_account_id: UUID
    to_account_id: Optional[UUID] = None
    amount: int = Field(..., gt=0)
    frequency: str = Field(..., pattern="^(daily|weekly|biweekly|monthly)$")
    description: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None

