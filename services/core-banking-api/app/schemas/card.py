"""
Card Schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID

from app.models.card import CardType, CardStatus, CardNetwork


class CardCreate(BaseModel):
    """Create card request"""
    account_id: UUID
    card_type: CardType
    card_network: CardNetwork = CardNetwork.VISA
    cardholder_name: str = Field(..., max_length=255)
    is_physical: bool = True
    billing_address: Optional[dict] = None
    shipping_address: Optional[dict] = None


class CardResponse(BaseModel):
    """Card response"""
    id: UUID
    user_id: UUID
    account_id: UUID
    card_number_last_four: str
    expiry_month: int
    expiry_year: int
    card_type: CardType
    card_network: CardNetwork
    cardholder_name: str
    status: CardStatus
    is_physical: bool
    pin_set: bool
    
    # Limits
    daily_limit: int
    transaction_limit: int
    monthly_limit: int
    atm_daily_limit: int
    
    # Controls
    online_transactions_enabled: bool
    international_transactions_enabled: bool
    contactless_enabled: bool
    atm_withdrawals_enabled: bool
    
    # Credit card
    credit_limit: Optional[int] = None
    current_balance: int = 0
    
    created_at: datetime
    activated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
    
    @property
    def masked_number(self) -> str:
        return f"**** **** **** {self.card_number_last_four}"


class CardListResponse(BaseModel):
    """List of cards"""
    cards: List[CardResponse]
    total: int


class CardActivateRequest(BaseModel):
    """Activate card request"""
    last_four_digits: str = Field(..., min_length=4, max_length=4)
    cvv: str = Field(..., min_length=3, max_length=4)


class CardSetPinRequest(BaseModel):
    """Set card PIN"""
    pin: str = Field(..., min_length=4, max_length=6)
    confirm_pin: str = Field(..., min_length=4, max_length=6)


class CardControlsUpdate(BaseModel):
    """Update card controls"""
    online_transactions_enabled: Optional[bool] = None
    international_transactions_enabled: Optional[bool] = None
    contactless_enabled: Optional[bool] = None
    atm_withdrawals_enabled: Optional[bool] = None


class CardLimitsUpdate(BaseModel):
    """Update card limits"""
    daily_limit: Optional[int] = Field(None, ge=0)
    transaction_limit: Optional[int] = Field(None, ge=0)
    monthly_limit: Optional[int] = Field(None, ge=0)
    atm_daily_limit: Optional[int] = Field(None, ge=0)


class CardBlockRequest(BaseModel):
    """Block card request"""
    reason: str = Field(..., pattern="^(lost|stolen|suspicious|temporary)$")
    notes: Optional[str] = None


class CardTransactionResponse(BaseModel):
    """Card transaction"""
    id: UUID
    card_id: UUID
    merchant_name: str
    merchant_category: str
    amount: int
    currency: str
    status: str
    is_international: bool
    location: Optional[str] = None
    created_at: datetime


class VirtualCardCreate(BaseModel):
    """Create virtual card"""
    account_id: UUID
    cardholder_name: str = Field(..., max_length=255)
    card_network: CardNetwork = CardNetwork.VISA
    daily_limit: int = Field(default=50000, ge=0)  # $500 default
    transaction_limit: int = Field(default=20000, ge=0)  # $200 default
    expiry_months: int = Field(default=12, ge=1, le=60)
    purpose: Optional[str] = None

