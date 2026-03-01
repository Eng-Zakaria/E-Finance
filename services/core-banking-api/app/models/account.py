"""
Account Model
Handles bank accounts, balances, and account operations
"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Integer, Numeric, Text, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum
from decimal import Decimal

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.transaction import Transaction
    from app.models.card import Card


class AccountType(str, enum.Enum):
    """Account type enumeration"""
    SAVINGS = "savings"
    CURRENT = "current"
    FIXED_DEPOSIT = "fixed_deposit"
    RECURRING_DEPOSIT = "recurring_deposit"
    LOAN = "loan"
    CREDIT = "credit"
    CRYPTO = "crypto"


class AccountStatus(str, enum.Enum):
    """Account status"""
    PENDING = "pending"
    ACTIVE = "active"
    DORMANT = "dormant"
    FROZEN = "frozen"
    CLOSED = "closed"


class Currency(str, enum.Enum):
    """Supported currencies"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    AED = "AED"
    SAR = "SAR"
    EGP = "EGP"
    BTC = "BTC"
    ETH = "ETH"
    USDT = "USDT"
    USDC = "USDC"


class Account(Base):
    """Bank Account Model"""
    __tablename__ = "accounts"
    
    __table_args__ = (
        Index("idx_accounts_user_id", "user_id"),
        Index("idx_accounts_account_number", "account_number"),
        Index("idx_accounts_status", "status"),
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
    
    # Account Details
    account_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    account_name: Mapped[str] = mapped_column(String(255))
    account_type: Mapped[AccountType] = mapped_column(SQLEnum(AccountType))
    currency: Mapped[Currency] = mapped_column(SQLEnum(Currency), default=Currency.USD)
    
    # Balances (stored in smallest unit - cents/satoshi)
    balance: Mapped[int] = mapped_column(Integer, default=0)
    available_balance: Mapped[int] = mapped_column(Integer, default=0)
    hold_balance: Mapped[int] = mapped_column(Integer, default=0)
    
    # For credit/loan accounts
    credit_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    minimum_balance: Mapped[int] = mapped_column(Integer, default=0)
    
    # Interest
    interest_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4), 
        nullable=True
    )  # e.g., 0.0350 = 3.50%
    interest_accrued: Mapped[int] = mapped_column(Integer, default=0)
    last_interest_calculated: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # Status
    status: Mapped[AccountStatus] = mapped_column(
        SQLEnum(AccountStatus), 
        default=AccountStatus.ACTIVE
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # International
    iban: Mapped[Optional[str]] = mapped_column(String(34), nullable=True)
    swift_code: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
    routing_number: Mapped[Optional[str]] = mapped_column(String(9), nullable=True)
    
    # Crypto specific
    wallet_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    blockchain_network: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Limits
    daily_transfer_limit: Mapped[int] = mapped_column(Integer, default=1000000)  # In cents
    daily_withdrawal_limit: Mapped[int] = mapped_column(Integer, default=500000)
    monthly_transfer_limit: Mapped[int] = mapped_column(Integer, default=10000000)
    
    # Usage tracking
    daily_transfer_used: Mapped[int] = mapped_column(Integer, default=0)
    daily_withdrawal_used: Mapped[int] = mapped_column(Integer, default=0)
    monthly_transfer_used: Mapped[int] = mapped_column(Integer, default=0)
    last_limit_reset: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
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
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="accounts")
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="account",
        foreign_keys="[Transaction.account_id]",
        cascade="all, delete-orphan"
    )
    cards: Mapped[List["Card"]] = relationship(
        "Card",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    
    @property
    def formatted_balance(self) -> str:
        """Get formatted balance"""
        if self.currency in [Currency.BTC, Currency.ETH]:
            # Crypto uses 8 decimal places
            return f"{self.balance / 100000000:.8f} {self.currency.value}"
        else:
            # Fiat uses 2 decimal places
            return f"{self.balance / 100:.2f} {self.currency.value}"
    
    def can_withdraw(self, amount: int) -> bool:
        """Check if withdrawal is allowed"""
        return (
            self.status == AccountStatus.ACTIVE and
            self.available_balance >= amount and
            self.available_balance - amount >= self.minimum_balance
        )
    
    def can_transfer(self, amount: int) -> bool:
        """Check if transfer is allowed"""
        return (
            self.status == AccountStatus.ACTIVE and
            self.available_balance >= amount and
            self.daily_transfer_used + amount <= self.daily_transfer_limit and
            self.monthly_transfer_used + amount <= self.monthly_transfer_limit
        )
    
    def __repr__(self):
        return f"<Account(id={self.id}, number={self.account_number}, type={self.account_type.value})>"

