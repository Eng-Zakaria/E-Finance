"""
Card Model
Handles debit and credit cards
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Integer, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.account import Account


class CardType(str, enum.Enum):
    """Card type enumeration"""
    DEBIT = "debit"
    CREDIT = "credit"
    PREPAID = "prepaid"
    VIRTUAL = "virtual"


class CardStatus(str, enum.Enum):
    """Card status"""
    PENDING = "pending"
    ACTIVE = "active"
    BLOCKED = "blocked"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    LOST = "lost"
    STOLEN = "stolen"


class CardNetwork(str, enum.Enum):
    """Card network"""
    VISA = "visa"
    MASTERCARD = "mastercard"
    AMEX = "amex"
    DISCOVER = "discover"


class Card(Base):
    """Card Model"""
    __tablename__ = "cards"
    
    __table_args__ = (
        Index("idx_cards_user_id", "user_id"),
        Index("idx_cards_account_id", "account_id"),
        Index("idx_cards_card_number_hash", "card_number_hash"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("accounts.id", ondelete="CASCADE"),
        index=True
    )
    
    # Card Details (encrypted/hashed in production)
    card_number_hash: Mapped[str] = mapped_column(String(255), index=True)
    card_number_last_four: Mapped[str] = mapped_column(String(4))
    expiry_month: Mapped[int] = mapped_column(Integer)
    expiry_year: Mapped[int] = mapped_column(Integer)
    cvv_hash: Mapped[str] = mapped_column(String(255))
    
    # Card Info
    card_type: Mapped[CardType] = mapped_column(SQLEnum(CardType))
    card_network: Mapped[CardNetwork] = mapped_column(SQLEnum(CardNetwork), default=CardNetwork.VISA)
    cardholder_name: Mapped[str] = mapped_column(String(255))
    
    # Status
    status: Mapped[CardStatus] = mapped_column(
        SQLEnum(CardStatus),
        default=CardStatus.ACTIVE
    )
    is_physical: Mapped[bool] = mapped_column(Boolean, default=True)
    pin_set: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Limits (in cents)
    daily_limit: Mapped[int] = mapped_column(Integer, default=500000)  # $5000
    transaction_limit: Mapped[int] = mapped_column(Integer, default=100000)  # $1000
    monthly_limit: Mapped[int] = mapped_column(Integer, default=5000000)  # $50000
    atm_daily_limit: Mapped[int] = mapped_column(Integer, default=100000)  # $1000
    
    # Usage tracking
    daily_spent: Mapped[int] = mapped_column(Integer, default=0)
    monthly_spent: Mapped[int] = mapped_column(Integer, default=0)
    last_limit_reset: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Controls
    online_transactions_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    international_transactions_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    contactless_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    atm_withdrawals_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Credit card specific
    credit_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_balance: Mapped[int] = mapped_column(Integer, default=0)
    minimum_payment: Mapped[int] = mapped_column(Integer, default=0)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Physical card shipping
    billing_address: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    shipping_address: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="cards")
    account: Mapped["Account"] = relationship("Account", back_populates="cards")
    
    @property
    def masked_number(self) -> str:
        """Get masked card number"""
        return f"**** **** **** {self.card_number_last_four}"
    
    @property
    def expiry_display(self) -> str:
        """Get expiry in MM/YY format"""
        return f"{self.expiry_month:02d}/{str(self.expiry_year)[-2:]}"
    
    @property
    def is_expired(self) -> bool:
        """Check if card is expired"""
        now = datetime.utcnow()
        expiry = datetime(self.expiry_year, self.expiry_month, 1)
        return now > expiry
    
    def can_transact(self, amount: int, is_international: bool = False, is_online: bool = False) -> bool:
        """Check if transaction is allowed"""
        if self.status != CardStatus.ACTIVE:
            return False
        if self.is_expired:
            return False
        if amount > self.transaction_limit:
            return False
        if self.daily_spent + amount > self.daily_limit:
            return False
        if is_international and not self.international_transactions_enabled:
            return False
        if is_online and not self.online_transactions_enabled:
            return False
        return True
    
    def __repr__(self):
        return f"<Card(id={self.id}, type={self.card_type.value}, last_four={self.card_number_last_four})>"

