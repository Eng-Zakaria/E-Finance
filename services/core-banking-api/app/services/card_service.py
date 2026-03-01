"""
Card Service
Handles card operations, controls, and transactions
"""
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID
import secrets
import hashlib
import random

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import structlog

from app.models.card import Card, CardType, CardStatus, CardNetwork
from app.models.account import Account, AccountStatus
from app.schemas.card import (
    CardCreate, CardResponse, CardListResponse,
    CardControlsUpdate, CardLimitsUpdate, VirtualCardCreate
)

logger = structlog.get_logger(__name__)


class CardService:
    """Card management service"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    @staticmethod
    def generate_card_number(network: CardNetwork) -> str:
        """Generate a valid card number (simplified Luhn algorithm)"""
        # Card prefixes by network
        prefixes = {
            CardNetwork.VISA: "4",
            CardNetwork.MASTERCARD: "5" + str(random.randint(1, 5)),
            CardNetwork.AMEX: "37",
            CardNetwork.DISCOVER: "6011"
        }
        
        prefix = prefixes.get(network, "4")
        remaining_length = 16 - len(prefix) - 1  # -1 for check digit
        
        number = prefix + "".join([str(random.randint(0, 9)) for _ in range(remaining_length)])
        
        # Calculate Luhn check digit
        digits = [int(d) for d in number]
        for i in range(len(digits) - 1, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9
        
        check_digit = (10 - (sum(digits) % 10)) % 10
        
        return number + str(check_digit)
    
    @staticmethod
    def generate_cvv() -> str:
        """Generate CVV"""
        return "".join([str(random.randint(0, 9)) for _ in range(3)])
    
    @staticmethod
    def hash_card_number(card_number: str) -> str:
        """Hash card number for storage"""
        return hashlib.sha256(card_number.encode()).hexdigest()
    
    @staticmethod
    def hash_cvv(cvv: str) -> str:
        """Hash CVV for storage"""
        return hashlib.sha256(cvv.encode()).hexdigest()
    
    async def create_card(
        self,
        user_id: UUID,
        data: CardCreate
    ) -> Tuple[Optional[dict], Optional[str]]:
        """Create a new card"""
        # Verify account ownership
        account_result = await self.session.execute(
            select(Account).where(
                and_(
                    Account.id == data.account_id,
                    Account.user_id == user_id
                )
            )
        )
        account = account_result.scalar_one_or_none()
        
        if not account:
            return None, "Account not found or not authorized"
        
        if account.status != AccountStatus.ACTIVE:
            return None, "Account is not active"
        
        # Check card limit
        existing_cards = await self.session.execute(
            select(func.count(Card.id)).where(
                and_(
                    Card.user_id == user_id,
                    Card.status.in_([CardStatus.ACTIVE, CardStatus.PENDING])
                )
            )
        )
        card_count = existing_cards.scalar()
        
        if card_count >= 5:
            return None, "Maximum card limit reached"
        
        # Generate card details
        card_number = self.generate_card_number(data.card_network)
        cvv = self.generate_cvv()
        
        # Set expiry (3 years from now)
        now = datetime.utcnow()
        expiry_year = now.year + 3
        expiry_month = now.month
        
        # Create card
        card = Card(
            user_id=user_id,
            account_id=data.account_id,
            card_number_hash=self.hash_card_number(card_number),
            card_number_last_four=card_number[-4:],
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            cvv_hash=self.hash_cvv(cvv),
            card_type=data.card_type,
            card_network=data.card_network,
            cardholder_name=data.cardholder_name.upper(),
            is_physical=data.is_physical,
            status=CardStatus.PENDING if data.is_physical else CardStatus.ACTIVE,
            billing_address=data.billing_address,
            shipping_address=data.shipping_address,
            activated_at=datetime.utcnow() if not data.is_physical else None
        )
        
        self.session.add(card)
        await self.session.commit()
        await self.session.refresh(card)
        
        logger.info(
            "Card created",
            card_id=str(card.id),
            user_id=str(user_id),
            type=data.card_type.value
        )
        
        # Return full card details only on creation
        return {
            "card_id": str(card.id),
            "card_number": card_number,  # Only shown once!
            "cvv": cvv,  # Only shown once!
            "expiry_month": expiry_month,
            "expiry_year": expiry_year,
            "cardholder_name": card.cardholder_name,
            "card_type": card.card_type.value,
            "card_network": card.card_network.value,
            "status": card.status.value,
            "message": "Card created successfully. Save these details securely - they won't be shown again."
        }, None
    
    async def create_virtual_card(
        self,
        user_id: UUID,
        data: VirtualCardCreate
    ) -> Tuple[Optional[dict], Optional[str]]:
        """Create a virtual card"""
        create_data = CardCreate(
            account_id=data.account_id,
            card_type=CardType.VIRTUAL,
            card_network=data.card_network,
            cardholder_name=data.cardholder_name,
            is_physical=False
        )
        
        result, error = await self.create_card(user_id, create_data)
        
        if error:
            return None, error
        
        # Update limits for virtual card
        card = await self.get_card(UUID(result["card_id"]))
        if card:
            card.daily_limit = data.daily_limit
            card.transaction_limit = data.transaction_limit
            await self.session.commit()
        
        return result, None
    
    async def get_card(self, card_id: UUID) -> Optional[Card]:
        """Get card by ID"""
        result = await self.session.execute(
            select(Card).where(Card.id == card_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_cards(self, user_id: UUID) -> CardListResponse:
        """Get all cards for a user"""
        result = await self.session.execute(
            select(Card)
            .where(Card.user_id == user_id)
            .order_by(Card.created_at.desc())
        )
        cards = list(result.scalars().all())
        
        return CardListResponse(
            cards=[CardResponse.model_validate(c) for c in cards],
            total=len(cards)
        )
    
    async def activate_card(
        self,
        card_id: UUID,
        user_id: UUID,
        last_four: str,
        cvv: str
    ) -> Tuple[bool, Optional[str]]:
        """Activate a physical card"""
        card = await self.get_card(card_id)
        
        if not card or card.user_id != user_id:
            return False, "Card not found"
        
        if card.status != CardStatus.PENDING:
            return False, "Card cannot be activated"
        
        # Verify last four digits
        if card.card_number_last_four != last_four:
            return False, "Invalid card details"
        
        # Verify CVV
        if card.cvv_hash != self.hash_cvv(cvv):
            return False, "Invalid CVV"
        
        card.status = CardStatus.ACTIVE
        card.activated_at = datetime.utcnow()
        
        await self.session.commit()
        
        logger.info("Card activated", card_id=str(card_id))
        
        return True, None
    
    async def set_pin(
        self,
        card_id: UUID,
        user_id: UUID,
        pin: str
    ) -> Tuple[bool, Optional[str]]:
        """Set or change card PIN"""
        card = await self.get_card(card_id)
        
        if not card or card.user_id != user_id:
            return False, "Card not found"
        
        if card.status != CardStatus.ACTIVE:
            return False, "Card is not active"
        
        # In production, PIN would be encrypted and stored securely
        card.pin_set = True
        await self.session.commit()
        
        logger.info("Card PIN set", card_id=str(card_id))
        
        return True, None
    
    async def update_controls(
        self,
        card_id: UUID,
        user_id: UUID,
        data: CardControlsUpdate
    ) -> Tuple[Optional[Card], Optional[str]]:
        """Update card controls"""
        card = await self.get_card(card_id)
        
        if not card or card.user_id != user_id:
            return None, "Card not found"
        
        # Update controls
        if data.online_transactions_enabled is not None:
            card.online_transactions_enabled = data.online_transactions_enabled
        if data.international_transactions_enabled is not None:
            card.international_transactions_enabled = data.international_transactions_enabled
        if data.contactless_enabled is not None:
            card.contactless_enabled = data.contactless_enabled
        if data.atm_withdrawals_enabled is not None:
            card.atm_withdrawals_enabled = data.atm_withdrawals_enabled
        
        card.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(card)
        
        logger.info("Card controls updated", card_id=str(card_id))
        
        return card, None
    
    async def update_limits(
        self,
        card_id: UUID,
        user_id: UUID,
        data: CardLimitsUpdate
    ) -> Tuple[Optional[Card], Optional[str]]:
        """Update card limits"""
        card = await self.get_card(card_id)
        
        if not card or card.user_id != user_id:
            return None, "Card not found"
        
        # Update limits
        if data.daily_limit is not None:
            card.daily_limit = data.daily_limit
        if data.transaction_limit is not None:
            card.transaction_limit = data.transaction_limit
        if data.monthly_limit is not None:
            card.monthly_limit = data.monthly_limit
        if data.atm_daily_limit is not None:
            card.atm_daily_limit = data.atm_daily_limit
        
        card.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(card)
        
        logger.info("Card limits updated", card_id=str(card_id))
        
        return card, None
    
    async def block_card(
        self,
        card_id: UUID,
        user_id: UUID,
        reason: str
    ) -> Tuple[bool, Optional[str]]:
        """Block a card"""
        card = await self.get_card(card_id)
        
        if not card or card.user_id != user_id:
            return False, "Card not found"
        
        if reason == "lost":
            card.status = CardStatus.LOST
        elif reason == "stolen":
            card.status = CardStatus.STOLEN
        elif reason == "suspicious":
            card.status = CardStatus.BLOCKED
        else:
            card.status = CardStatus.BLOCKED
        
        card.updated_at = datetime.utcnow()
        await self.session.commit()
        
        logger.warning(
            "Card blocked",
            card_id=str(card_id),
            reason=reason
        )
        
        return True, None
    
    async def unblock_card(
        self,
        card_id: UUID,
        user_id: UUID
    ) -> Tuple[bool, Optional[str]]:
        """Unblock a card (only if temporarily blocked)"""
        card = await self.get_card(card_id)
        
        if not card or card.user_id != user_id:
            return False, "Card not found"
        
        if card.status not in [CardStatus.BLOCKED]:
            return False, "Card cannot be unblocked"
        
        card.status = CardStatus.ACTIVE
        card.updated_at = datetime.utcnow()
        await self.session.commit()
        
        logger.info("Card unblocked", card_id=str(card_id))
        
        return True, None
    
    async def cancel_card(
        self,
        card_id: UUID,
        user_id: UUID
    ) -> Tuple[bool, Optional[str]]:
        """Permanently cancel a card"""
        card = await self.get_card(card_id)
        
        if not card or card.user_id != user_id:
            return False, "Card not found"
        
        if card.status == CardStatus.CANCELLED:
            return False, "Card already cancelled"
        
        card.status = CardStatus.CANCELLED
        card.updated_at = datetime.utcnow()
        await self.session.commit()
        
        logger.info("Card cancelled", card_id=str(card_id))
        
        return True, None
    
    async def reset_daily_limits(self):
        """Reset daily spending limits (called by scheduler)"""
        await self.session.execute(
            Card.__table__.update().values(
                daily_spent=0,
                last_limit_reset=datetime.utcnow()
            )
        )
        await self.session.commit()
        logger.info("Daily card limits reset")
    
    async def reset_monthly_limits(self):
        """Reset monthly spending limits (called by scheduler)"""
        await self.session.execute(
            Card.__table__.update().values(
                monthly_spent=0
            )
        )
        await self.session.commit()
        logger.info("Monthly card limits reset")

