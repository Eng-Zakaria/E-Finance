"""
Transaction Model
Handles all financial transactions with fraud detection markers
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Integer, Text, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum

from app.database import Base

if TYPE_CHECKING:
    from app.models.account import Account


class TransactionType(str, enum.Enum):
    """Transaction type enumeration"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    PAYMENT = "payment"
    REFUND = "refund"
    FEE = "fee"
    INTEREST = "interest"
    LOAN_DISBURSEMENT = "loan_disbursement"
    LOAN_REPAYMENT = "loan_repayment"
    CRYPTO_BUY = "crypto_buy"
    CRYPTO_SELL = "crypto_sell"
    CRYPTO_TRANSFER = "crypto_transfer"
    BNPL_PURCHASE = "bnpl_purchase"
    BNPL_INSTALLMENT = "bnpl_installment"
    CARD_PURCHASE = "card_purchase"
    ATM_WITHDRAWAL = "atm_withdrawal"
    INTERNATIONAL_TRANSFER = "international_transfer"


class TransactionStatus(str, enum.Enum):
    """Transaction status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"
    ON_HOLD = "on_hold"
    FLAGGED = "flagged"  # Flagged for review


class TransactionChannel(str, enum.Enum):
    """Channel through which transaction was initiated"""
    WEB = "web"
    MOBILE = "mobile"
    API = "api"
    ATM = "atm"
    POS = "pos"
    BRANCH = "branch"
    AUTOMATED = "automated"


class RiskLevel(str, enum.Enum):
    """Transaction risk level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Transaction(Base):
    """Financial Transaction Model"""
    __tablename__ = "transactions"
    
    __table_args__ = (
        Index("idx_transactions_account_id", "account_id"),
        Index("idx_transactions_created_at", "created_at"),
        Index("idx_transactions_status", "status"),
        Index("idx_transactions_type", "transaction_type"),
        Index("idx_transactions_reference", "reference_number"),
        Index("idx_transactions_risk_level", "risk_level"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # Account references
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("accounts.id", ondelete="CASCADE"),
        index=True
    )
    counterparty_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Transaction Details
    reference_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    transaction_type: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType))
    channel: Mapped[TransactionChannel] = mapped_column(
        SQLEnum(TransactionChannel),
        default=TransactionChannel.WEB
    )
    
    # Amount (in smallest unit - cents/satoshi)
    amount: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10))
    fee: Mapped[int] = mapped_column(Integer, default=0)
    
    # For international/crypto transactions
    exchange_rate: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    original_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    original_currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Balance tracking
    balance_before: Mapped[int] = mapped_column(Integer)
    balance_after: Mapped[int] = mapped_column(Integer)
    
    # Status
    status: Mapped[TransactionStatus] = mapped_column(
        SQLEnum(TransactionStatus),
        default=TransactionStatus.PENDING
    )
    
    # Counterparty info (for external transfers)
    counterparty_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    counterparty_bank: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    counterparty_account: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    counterparty_iban: Mapped[Optional[str]] = mapped_column(String(34), nullable=True)
    counterparty_swift: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
    
    # Crypto specific
    blockchain_tx_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    blockchain_network: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    wallet_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gas_fee: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Description and notes
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    memo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Location/Device info
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    device_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location_country: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    location_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    geolocation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # lat,lng
    
    # Fraud Detection Fields
    risk_level: Mapped[RiskLevel] = mapped_column(
        SQLEnum(RiskLevel),
        default=RiskLevel.LOW
    )
    risk_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    fraud_flags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # AML specific
    aml_check_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    aml_alert_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pep_screening_result: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sanctions_screening_result: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
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
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="transactions",
        foreign_keys=[account_id]
    )
    counterparty_account_rel: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[counterparty_account_id]
    )
    
    @property
    def formatted_amount(self) -> str:
        """Get formatted amount"""
        return f"{self.amount / 100:.2f} {self.currency}"
    
    @property
    def is_debit(self) -> bool:
        """Check if transaction is a debit"""
        return self.transaction_type in [
            TransactionType.WITHDRAWAL,
            TransactionType.TRANSFER_OUT,
            TransactionType.PAYMENT,
            TransactionType.FEE,
            TransactionType.LOAN_REPAYMENT,
            TransactionType.CRYPTO_BUY,
            TransactionType.CARD_PURCHASE,
            TransactionType.ATM_WITHDRAWAL,
            TransactionType.INTERNATIONAL_TRANSFER,
            TransactionType.BNPL_INSTALLMENT,
        ]
    
    @property
    def is_credit(self) -> bool:
        """Check if transaction is a credit"""
        return not self.is_debit
    
    @property
    def requires_review(self) -> bool:
        """Check if transaction requires manual review"""
        return (
            self.is_suspicious or
            self.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] or
            self.status == TransactionStatus.FLAGGED
        )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, ref={self.reference_number}, type={self.transaction_type.value}, amount={self.formatted_amount})>"

