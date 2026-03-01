"""
Account Schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID
from decimal import Decimal

from app.models.account import AccountType, AccountStatus, Currency


class AccountCreate(BaseModel):
    """Create account request"""
    account_name: str = Field(..., min_length=1, max_length=255)
    account_type: AccountType
    currency: Currency = Currency.USD
    is_primary: bool = False


class AccountResponse(BaseModel):
    """Account response"""
    id: UUID
    user_id: UUID
    account_number: str
    account_name: str
    account_type: AccountType
    currency: Currency
    balance: int
    available_balance: int
    hold_balance: int
    interest_rate: Optional[Decimal] = None
    status: AccountStatus
    is_primary: bool
    iban: Optional[str] = None
    swift_code: Optional[str] = None
    wallet_address: Optional[str] = None
    blockchain_network: Optional[str] = None
    daily_transfer_limit: int
    daily_withdrawal_limit: int
    monthly_transfer_limit: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
    
    @property
    def formatted_balance(self) -> str:
        """Get formatted balance"""
        if self.currency in [Currency.BTC, Currency.ETH]:
            return f"{self.balance / 100000000:.8f} {self.currency.value}"
        return f"{self.balance / 100:.2f} {self.currency.value}"


class AccountListResponse(BaseModel):
    """List of accounts response"""
    accounts: List[AccountResponse]
    total: int


class AccountBalanceResponse(BaseModel):
    """Account balance response"""
    account_id: UUID
    account_number: str
    currency: Currency
    balance: int
    available_balance: int
    hold_balance: int
    as_of: datetime


class AccountStatementRequest(BaseModel):
    """Account statement request"""
    start_date: datetime
    end_date: datetime
    format: str = Field(default="json", pattern="^(json|pdf|csv)$")


class AccountUpdateRequest(BaseModel):
    """Update account request"""
    account_name: Optional[str] = Field(None, max_length=255)
    is_primary: Optional[bool] = None


class AccountLimitsUpdate(BaseModel):
    """Update account limits"""
    daily_transfer_limit: Optional[int] = Field(None, ge=0)
    daily_withdrawal_limit: Optional[int] = Field(None, ge=0)
    monthly_transfer_limit: Optional[int] = Field(None, ge=0)


class DepositRequest(BaseModel):
    """Deposit funds request"""
    amount: int = Field(..., gt=0, description="Amount in cents")
    description: Optional[str] = None
    reference: Optional[str] = None


class WithdrawalRequest(BaseModel):
    """Withdraw funds request"""
    amount: int = Field(..., gt=0, description="Amount in cents")
    description: Optional[str] = None
    pin: Optional[str] = Field(None, min_length=4, max_length=6)


class TransferRequest(BaseModel):
    """Internal transfer request"""
    from_account_id: UUID
    to_account_id: UUID
    amount: int = Field(..., gt=0, description="Amount in cents")
    description: Optional[str] = None
    memo: Optional[str] = Field(None, max_length=255)
    scheduled_at: Optional[datetime] = None


class ExternalTransferRequest(BaseModel):
    """External bank transfer request"""
    from_account_id: UUID
    amount: int = Field(..., gt=0, description="Amount in cents")
    currency: Currency
    
    # Recipient details
    recipient_name: str = Field(..., max_length=255)
    recipient_bank: str = Field(..., max_length=255)
    recipient_account: str = Field(..., max_length=50)
    recipient_iban: Optional[str] = Field(None, max_length=34)
    recipient_swift: Optional[str] = Field(None, max_length=11)
    recipient_routing: Optional[str] = Field(None, max_length=9)
    recipient_country: str = Field(..., max_length=3)
    
    # Transfer details
    description: Optional[str] = None
    memo: Optional[str] = Field(None, max_length=255)
    transfer_type: str = Field(default="standard", pattern="^(standard|express|same_day)$")


class TransferResponse(BaseModel):
    """Transfer response"""
    transaction_id: UUID
    reference_number: str
    status: str
    amount: int
    currency: str
    fee: int
    from_account: str
    to_account: str
    description: Optional[str] = None
    estimated_arrival: Optional[datetime] = None
    created_at: datetime


class BillPaymentRequest(BaseModel):
    """Bill payment request"""
    from_account_id: UUID
    biller_code: str = Field(..., max_length=50)
    biller_name: str = Field(..., max_length=255)
    reference_number: str = Field(..., max_length=100)
    amount: int = Field(..., gt=0)
    description: Optional[str] = None


class ScheduledPaymentCreate(BaseModel):
    """Create scheduled/recurring payment"""
    from_account_id: UUID
    to_account_id: Optional[UUID] = None
    
    # External recipient
    recipient_name: Optional[str] = None
    recipient_account: Optional[str] = None
    recipient_bank: Optional[str] = None
    
    amount: int = Field(..., gt=0)
    currency: Currency = Currency.USD
    description: Optional[str] = None
    
    # Schedule
    frequency: str = Field(..., pattern="^(once|daily|weekly|biweekly|monthly|quarterly|yearly)$")
    start_date: datetime
    end_date: Optional[datetime] = None
    day_of_month: Optional[int] = Field(None, ge=1, le=28)


class ScheduledPaymentResponse(BaseModel):
    """Scheduled payment response"""
    id: UUID
    from_account_id: UUID
    amount: int
    currency: Currency
    frequency: str
    next_payment_date: datetime
    status: str
    total_payments_made: int
    created_at: datetime

