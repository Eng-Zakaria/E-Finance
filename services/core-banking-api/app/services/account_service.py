"""
Account Service
Handles bank accounts, balances, and account operations
"""
from datetime import datetime, date
from typing import Optional, List, Tuple
from uuid import UUID
import random
import string
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
import structlog

from app.config import settings
from app.models.account import Account, AccountType, AccountStatus, Currency
from app.models.transaction import Transaction, TransactionType, TransactionStatus, TransactionChannel
from app.schemas.account import (
    AccountCreate, AccountResponse, AccountListResponse, AccountBalanceResponse,
    TransferRequest, TransferResponse, DepositRequest, WithdrawalRequest,
    ExternalTransferRequest
)

logger = structlog.get_logger(__name__)


class AccountService:
    """Account management service"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    @staticmethod
    def generate_account_number() -> str:
        """Generate unique account number"""
        # Format: EFIN + 12 random digits
        return "EFIN" + "".join(random.choices(string.digits, k=12))
    
    @staticmethod
    def generate_iban(account_number: str, country: str = "AE") -> str:
        """Generate IBAN (simplified)"""
        # Simplified IBAN generation - in production use proper algorithm
        return f"{country}89EFIN{account_number[-12:].zfill(16)}"
    
    @staticmethod
    def generate_reference_number() -> str:
        """Generate transaction reference number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"TXN{timestamp}{random_suffix}"
    
    async def create_account(
        self,
        user_id: UUID,
        data: AccountCreate
    ) -> Tuple[Optional[Account], Optional[str]]:
        """Create a new bank account"""
        # Check account limits per user
        existing_count = await self.session.execute(
            select(func.count(Account.id)).where(
                and_(
                    Account.user_id == user_id,
                    Account.status != AccountStatus.CLOSED
                )
            )
        )
        count = existing_count.scalar()
        
        if count >= 10:
            return None, "Maximum account limit reached"
        
        # Check if primary account already exists
        if data.is_primary:
            existing_primary = await self.session.execute(
                select(Account).where(
                    and_(
                        Account.user_id == user_id,
                        Account.is_primary == True,
                        Account.status == AccountStatus.ACTIVE
                    )
                )
            )
            if existing_primary.scalar_one_or_none():
                return None, "Primary account already exists"
        
        # Generate account number
        account_number = self.generate_account_number()
        
        # Create account
        account = Account(
            user_id=user_id,
            account_number=account_number,
            account_name=data.account_name,
            account_type=data.account_type,
            currency=data.currency,
            is_primary=data.is_primary,
            status=AccountStatus.ACTIVE,
            iban=self.generate_iban(account_number),
            swift_code="EFINAEAD",  # Example SWIFT code
            daily_transfer_limit=settings.DEFAULT_DAILY_TRANSFER_LIMIT,
            daily_withdrawal_limit=settings.DEFAULT_DAILY_WITHDRAWAL_LIMIT,
            monthly_transfer_limit=settings.DEFAULT_MONTHLY_TRANSFER_LIMIT,
        )
        
        # Set interest rate based on account type
        if data.account_type == AccountType.SAVINGS:
            account.interest_rate = Decimal("0.0250")  # 2.5%
        elif data.account_type == AccountType.FIXED_DEPOSIT:
            account.interest_rate = Decimal("0.0450")  # 4.5%
        
        self.session.add(account)
        await self.session.commit()
        await self.session.refresh(account)
        
        logger.info(
            "Account created",
            account_id=str(account.id),
            user_id=str(user_id),
            type=data.account_type.value
        )
        
        return account, None
    
    async def get_account(self, account_id: UUID) -> Optional[Account]:
        """Get account by ID"""
        result = await self.session.execute(
            select(Account).where(Account.id == account_id)
        )
        return result.scalar_one_or_none()
    
    async def get_account_by_number(self, account_number: str) -> Optional[Account]:
        """Get account by account number"""
        result = await self.session.execute(
            select(Account).where(Account.account_number == account_number)
        )
        return result.scalar_one_or_none()
    
    async def get_user_accounts(self, user_id: UUID) -> AccountListResponse:
        """Get all accounts for a user"""
        result = await self.session.execute(
            select(Account)
            .where(Account.user_id == user_id)
            .order_by(Account.is_primary.desc(), Account.created_at)
        )
        accounts = list(result.scalars().all())
        
        return AccountListResponse(
            accounts=[AccountResponse.model_validate(a) for a in accounts],
            total=len(accounts)
        )
    
    async def get_balance(self, account_id: UUID) -> Optional[AccountBalanceResponse]:
        """Get account balance"""
        account = await self.get_account(account_id)
        
        if not account:
            return None
        
        return AccountBalanceResponse(
            account_id=account.id,
            account_number=account.account_number,
            currency=account.currency,
            balance=account.balance,
            available_balance=account.available_balance,
            hold_balance=account.hold_balance,
            as_of=datetime.utcnow()
        )
    
    async def deposit(
        self,
        account_id: UUID,
        data: DepositRequest,
        channel: TransactionChannel = TransactionChannel.WEB
    ) -> Tuple[Optional[TransferResponse], Optional[str]]:
        """Deposit funds into account"""
        account = await self.get_account(account_id)
        
        if not account:
            return None, "Account not found"
        
        if account.status != AccountStatus.ACTIVE:
            return None, "Account is not active"
        
        # Create transaction
        reference = self.generate_reference_number()
        balance_before = account.balance
        
        transaction = Transaction(
            account_id=account.id,
            reference_number=reference,
            transaction_type=TransactionType.DEPOSIT,
            channel=channel,
            amount=data.amount,
            currency=account.currency.value,
            fee=0,
            balance_before=balance_before,
            balance_after=balance_before + data.amount,
            status=TransactionStatus.COMPLETED,
            description=data.description or "Cash deposit",
            completed_at=datetime.utcnow()
        )
        
        # Update account balance
        account.balance += data.amount
        account.available_balance += data.amount
        
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        
        logger.info(
            "Deposit completed",
            transaction_id=str(transaction.id),
            account_id=str(account_id),
            amount=data.amount
        )
        
        return TransferResponse(
            transaction_id=transaction.id,
            reference_number=reference,
            status="completed",
            amount=data.amount,
            currency=account.currency.value,
            fee=0,
            from_account="EXTERNAL",
            to_account=account.account_number,
            description=data.description,
            created_at=transaction.created_at
        ), None
    
    async def withdraw(
        self,
        account_id: UUID,
        data: WithdrawalRequest,
        channel: TransactionChannel = TransactionChannel.WEB
    ) -> Tuple[Optional[TransferResponse], Optional[str]]:
        """Withdraw funds from account"""
        account = await self.get_account(account_id)
        
        if not account:
            return None, "Account not found"
        
        if not account.can_withdraw(data.amount):
            return None, "Insufficient balance or withdrawal not allowed"
        
        # Check daily limit
        if account.daily_withdrawal_used + data.amount > account.daily_withdrawal_limit:
            return None, "Daily withdrawal limit exceeded"
        
        # Create transaction
        reference = self.generate_reference_number()
        balance_before = account.balance
        
        transaction = Transaction(
            account_id=account.id,
            reference_number=reference,
            transaction_type=TransactionType.WITHDRAWAL,
            channel=channel,
            amount=data.amount,
            currency=account.currency.value,
            fee=0,
            balance_before=balance_before,
            balance_after=balance_before - data.amount,
            status=TransactionStatus.COMPLETED,
            description=data.description or "Cash withdrawal",
            completed_at=datetime.utcnow()
        )
        
        # Update account balance
        account.balance -= data.amount
        account.available_balance -= data.amount
        account.daily_withdrawal_used += data.amount
        
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        
        logger.info(
            "Withdrawal completed",
            transaction_id=str(transaction.id),
            account_id=str(account_id),
            amount=data.amount
        )
        
        return TransferResponse(
            transaction_id=transaction.id,
            reference_number=reference,
            status="completed",
            amount=data.amount,
            currency=account.currency.value,
            fee=0,
            from_account=account.account_number,
            to_account="EXTERNAL",
            description=data.description,
            created_at=transaction.created_at
        ), None
    
    async def internal_transfer(
        self,
        user_id: UUID,
        data: TransferRequest
    ) -> Tuple[Optional[TransferResponse], Optional[str]]:
        """Transfer funds between internal accounts"""
        from_account = await self.get_account(data.from_account_id)
        to_account = await self.get_account(data.to_account_id)
        
        if not from_account:
            return None, "Source account not found"
        
        if not to_account:
            return None, "Destination account not found"
        
        # Verify ownership
        if from_account.user_id != user_id:
            return None, "Not authorized to transfer from this account"
        
        # Check if transfer is allowed
        if not from_account.can_transfer(data.amount):
            return None, "Transfer not allowed. Check balance or limits."
        
        # Currency conversion would happen here for cross-currency transfers
        if from_account.currency != to_account.currency:
            return None, "Cross-currency transfers not yet supported"
        
        # Generate reference
        reference = self.generate_reference_number()
        
        # Create debit transaction (from account)
        debit_tx = Transaction(
            account_id=from_account.id,
            counterparty_account_id=to_account.id,
            reference_number=reference,
            transaction_type=TransactionType.TRANSFER_OUT,
            channel=TransactionChannel.WEB,
            amount=data.amount,
            currency=from_account.currency.value,
            fee=0,
            balance_before=from_account.balance,
            balance_after=from_account.balance - data.amount,
            status=TransactionStatus.COMPLETED,
            description=data.description or f"Transfer to {to_account.account_number}",
            memo=data.memo,
            counterparty_name="Internal Transfer",
            counterparty_account=to_account.account_number,
            completed_at=datetime.utcnow()
        )
        
        # Create credit transaction (to account)
        credit_reference = self.generate_reference_number()
        credit_tx = Transaction(
            account_id=to_account.id,
            counterparty_account_id=from_account.id,
            reference_number=credit_reference,
            transaction_type=TransactionType.TRANSFER_IN,
            channel=TransactionChannel.WEB,
            amount=data.amount,
            currency=to_account.currency.value,
            fee=0,
            balance_before=to_account.balance,
            balance_after=to_account.balance + data.amount,
            status=TransactionStatus.COMPLETED,
            description=data.description or f"Transfer from {from_account.account_number}",
            memo=data.memo,
            counterparty_name="Internal Transfer",
            counterparty_account=from_account.account_number,
            completed_at=datetime.utcnow()
        )
        
        # Update balances
        from_account.balance -= data.amount
        from_account.available_balance -= data.amount
        from_account.daily_transfer_used += data.amount
        from_account.monthly_transfer_used += data.amount
        
        to_account.balance += data.amount
        to_account.available_balance += data.amount
        
        self.session.add(debit_tx)
        self.session.add(credit_tx)
        await self.session.commit()
        await self.session.refresh(debit_tx)
        
        logger.info(
            "Internal transfer completed",
            transaction_id=str(debit_tx.id),
            from_account=str(from_account.id),
            to_account=str(to_account.id),
            amount=data.amount
        )
        
        return TransferResponse(
            transaction_id=debit_tx.id,
            reference_number=reference,
            status="completed",
            amount=data.amount,
            currency=from_account.currency.value,
            fee=0,
            from_account=from_account.account_number,
            to_account=to_account.account_number,
            description=data.description,
            created_at=debit_tx.created_at
        ), None
    
    async def external_transfer(
        self,
        user_id: UUID,
        data: ExternalTransferRequest
    ) -> Tuple[Optional[TransferResponse], Optional[str]]:
        """Transfer funds to external bank account"""
        from_account = await self.get_account(data.from_account_id)
        
        if not from_account:
            return None, "Source account not found"
        
        if from_account.user_id != user_id:
            return None, "Not authorized to transfer from this account"
        
        # Calculate fee based on transfer type
        fee = 0
        if data.transfer_type == "express":
            fee = 2500  # $25
        elif data.transfer_type == "same_day":
            fee = 1500  # $15
        else:
            fee = 500  # $5 standard
        
        # International transfer additional fee
        if data.recipient_country != "US":
            fee += 2500  # Additional $25 for international
        
        total_amount = data.amount + fee
        
        if not from_account.can_transfer(total_amount):
            return None, "Insufficient balance for transfer and fees"
        
        # Create transaction
        reference = self.generate_reference_number()
        
        transaction = Transaction(
            account_id=from_account.id,
            reference_number=reference,
            transaction_type=TransactionType.INTERNATIONAL_TRANSFER if data.recipient_country != "US" else TransactionType.TRANSFER_OUT,
            channel=TransactionChannel.WEB,
            amount=data.amount,
            currency=data.currency.value,
            fee=fee,
            balance_before=from_account.balance,
            balance_after=from_account.balance - total_amount,
            status=TransactionStatus.PROCESSING,  # External transfers need processing
            description=data.description or f"Transfer to {data.recipient_name}",
            memo=data.memo,
            counterparty_name=data.recipient_name,
            counterparty_bank=data.recipient_bank,
            counterparty_account=data.recipient_account,
            counterparty_iban=data.recipient_iban,
            counterparty_swift=data.recipient_swift,
            location_country=data.recipient_country
        )
        
        # Update balance
        from_account.balance -= total_amount
        from_account.available_balance -= total_amount
        from_account.daily_transfer_used += data.amount
        from_account.monthly_transfer_used += data.amount
        
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        
        # Calculate estimated arrival
        if data.transfer_type == "express":
            estimated_arrival = datetime.utcnow().replace(hour=23, minute=59)
        elif data.transfer_type == "same_day":
            from datetime import timedelta
            estimated_arrival = datetime.utcnow() + timedelta(hours=4)
        else:
            from datetime import timedelta
            estimated_arrival = datetime.utcnow() + timedelta(days=2 if data.recipient_country == "US" else 5)
        
        logger.info(
            "External transfer initiated",
            transaction_id=str(transaction.id),
            from_account=str(from_account.id),
            recipient=data.recipient_name,
            amount=data.amount
        )
        
        return TransferResponse(
            transaction_id=transaction.id,
            reference_number=reference,
            status="processing",
            amount=data.amount,
            currency=data.currency.value,
            fee=fee,
            from_account=from_account.account_number,
            to_account=data.recipient_account,
            description=data.description,
            estimated_arrival=estimated_arrival,
            created_at=transaction.created_at
        ), None
    
    async def calculate_interest(self, account_id: UUID) -> Tuple[int, Optional[str]]:
        """Calculate and credit interest for savings accounts"""
        account = await self.get_account(account_id)
        
        if not account:
            return 0, "Account not found"
        
        if account.account_type not in [AccountType.SAVINGS, AccountType.FIXED_DEPOSIT]:
            return 0, "Account type does not earn interest"
        
        if not account.interest_rate:
            return 0, "No interest rate set"
        
        # Calculate daily interest
        # Interest = Principal × Rate × Time (in years)
        # For daily: Interest = Principal × (Rate / 365)
        daily_interest = int(
            account.balance * (account.interest_rate / Decimal("365"))
        )
        
        account.interest_accrued += daily_interest
        account.last_interest_calculated = datetime.utcnow()
        
        await self.session.commit()
        
        return daily_interest, None
    
    async def credit_accrued_interest(self, account_id: UUID) -> Tuple[int, Optional[str]]:
        """Credit accrued interest to account (monthly)"""
        account = await self.get_account(account_id)
        
        if not account:
            return 0, "Account not found"
        
        if account.interest_accrued <= 0:
            return 0, "No accrued interest"
        
        # Create interest transaction
        reference = self.generate_reference_number()
        interest_amount = account.interest_accrued
        
        transaction = Transaction(
            account_id=account.id,
            reference_number=reference,
            transaction_type=TransactionType.INTEREST,
            channel=TransactionChannel.AUTOMATED,
            amount=interest_amount,
            currency=account.currency.value,
            fee=0,
            balance_before=account.balance,
            balance_after=account.balance + interest_amount,
            status=TransactionStatus.COMPLETED,
            description="Monthly interest credit",
            completed_at=datetime.utcnow()
        )
        
        # Update balance
        account.balance += interest_amount
        account.available_balance += interest_amount
        account.interest_accrued = 0
        
        self.session.add(transaction)
        await self.session.commit()
        
        logger.info(
            "Interest credited",
            account_id=str(account_id),
            amount=interest_amount
        )
        
        return interest_amount, None
    
    async def close_account(self, account_id: UUID, user_id: UUID) -> Tuple[bool, Optional[str]]:
        """Close an account"""
        account = await self.get_account(account_id)
        
        if not account:
            return False, "Account not found"
        
        if account.user_id != user_id:
            return False, "Not authorized"
        
        if account.balance > 0:
            return False, "Cannot close account with positive balance"
        
        if account.is_primary:
            return False, "Cannot close primary account"
        
        account.status = AccountStatus.CLOSED
        account.closed_at = datetime.utcnow()
        
        await self.session.commit()
        
        logger.info("Account closed", account_id=str(account_id))
        
        return True, None

