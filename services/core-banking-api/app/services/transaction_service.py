"""
Transaction Service
Handles transaction queries, analytics, and fraud monitoring
"""
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload
import structlog

from app.models.transaction import Transaction, TransactionType, TransactionStatus, RiskLevel
from app.models.account import Account
from app.schemas.transaction import (
    TransactionResponse, TransactionListResponse, TransactionFilterParams,
    TransactionAnalytics, FraudAlertResponse, DisputeRequest, DisputeResponse
)

logger = structlog.get_logger(__name__)


class TransactionService:
    """Transaction management service"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_transaction(self, transaction_id: UUID) -> Optional[Transaction]:
        """Get transaction by ID"""
        result = await self.session.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        return result.scalar_one_or_none()
    
    async def get_transaction_by_reference(self, reference: str) -> Optional[Transaction]:
        """Get transaction by reference number"""
        result = await self.session.execute(
            select(Transaction).where(Transaction.reference_number == reference)
        )
        return result.scalar_one_or_none()
    
    async def get_transactions(
        self,
        user_id: UUID,
        filters: TransactionFilterParams,
        page: int = 1,
        page_size: int = 20
    ) -> TransactionListResponse:
        """Get paginated transactions with filters"""
        # Get user's account IDs
        accounts_result = await self.session.execute(
            select(Account.id).where(Account.user_id == user_id)
        )
        account_ids = [row[0] for row in accounts_result.all()]
        
        if not account_ids:
            return TransactionListResponse(
                transactions=[],
                total=0,
                page=page,
                page_size=page_size
            )
        
        # Build query
        query = select(Transaction).where(Transaction.account_id.in_(account_ids))
        count_query = select(func.count(Transaction.id)).where(
            Transaction.account_id.in_(account_ids)
        )
        
        # Apply filters
        if filters.account_id:
            query = query.where(Transaction.account_id == filters.account_id)
            count_query = count_query.where(Transaction.account_id == filters.account_id)
        
        if filters.transaction_type:
            query = query.where(Transaction.transaction_type == filters.transaction_type)
            count_query = count_query.where(Transaction.transaction_type == filters.transaction_type)
        
        if filters.status:
            query = query.where(Transaction.status == filters.status)
            count_query = count_query.where(Transaction.status == filters.status)
        
        if filters.min_amount:
            query = query.where(Transaction.amount >= filters.min_amount)
            count_query = count_query.where(Transaction.amount >= filters.min_amount)
        
        if filters.max_amount:
            query = query.where(Transaction.amount <= filters.max_amount)
            count_query = count_query.where(Transaction.amount <= filters.max_amount)
        
        if filters.start_date:
            query = query.where(Transaction.created_at >= filters.start_date)
            count_query = count_query.where(Transaction.created_at >= filters.start_date)
        
        if filters.end_date:
            query = query.where(Transaction.created_at <= filters.end_date)
            count_query = count_query.where(Transaction.created_at <= filters.end_date)
        
        if filters.risk_level:
            query = query.where(Transaction.risk_level == filters.risk_level)
            count_query = count_query.where(Transaction.risk_level == filters.risk_level)
        
        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        query = (
            query
            .order_by(Transaction.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        
        result = await self.session.execute(query)
        transactions = result.scalars().all()
        
        return TransactionListResponse(
            transactions=[TransactionResponse.model_validate(t) for t in transactions],
            total=total,
            page=page,
            page_size=page_size
        )
    
    async def get_account_transactions(
        self,
        account_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Transaction]:
        """Get transactions for a specific account"""
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.account_id == account_id)
            .order_by(Transaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def search_transactions(
        self,
        user_id: UUID,
        query: str,
        limit: int = 50
    ) -> List[Transaction]:
        """Search transactions by reference, description, or counterparty"""
        # Get user's account IDs
        accounts_result = await self.session.execute(
            select(Account.id).where(Account.user_id == user_id)
        )
        account_ids = [row[0] for row in accounts_result.all()]
        
        if not account_ids:
            return []
        
        search_filter = or_(
            Transaction.reference_number.ilike(f"%{query}%"),
            Transaction.description.ilike(f"%{query}%"),
            Transaction.counterparty_name.ilike(f"%{query}%"),
            Transaction.memo.ilike(f"%{query}%")
        )
        
        result = await self.session.execute(
            select(Transaction)
            .where(
                and_(
                    Transaction.account_id.in_(account_ids),
                    search_filter
                )
            )
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_analytics(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> TransactionAnalytics:
        """Get transaction analytics for a user"""
        # Get user's account IDs
        accounts_result = await self.session.execute(
            select(Account.id).where(Account.user_id == user_id)
        )
        account_ids = [row[0] for row in accounts_result.all()]
        
        if not account_ids:
            return TransactionAnalytics(
                total_transactions=0,
                total_credits=0,
                total_debits=0,
                net_flow=0,
                average_transaction_amount=0,
                largest_transaction=0,
                transaction_by_type={},
                transaction_by_status={},
                daily_volume=[]
            )
        
        date_filter = and_(
            Transaction.account_id.in_(account_ids),
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date,
            Transaction.status == TransactionStatus.COMPLETED
        )
        
        # Total transactions
        total_result = await self.session.execute(
            select(func.count(Transaction.id)).where(date_filter)
        )
        total_transactions = total_result.scalar() or 0
        
        # Credits and debits
        credit_types = [
            TransactionType.DEPOSIT,
            TransactionType.TRANSFER_IN,
            TransactionType.REFUND,
            TransactionType.INTEREST,
            TransactionType.CRYPTO_SELL
        ]
        
        credits_result = await self.session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                and_(
                    date_filter,
                    Transaction.transaction_type.in_(credit_types)
                )
            )
        )
        total_credits = credits_result.scalar() or 0
        
        debits_result = await self.session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                and_(
                    date_filter,
                    ~Transaction.transaction_type.in_(credit_types)
                )
            )
        )
        total_debits = debits_result.scalar() or 0
        
        # Average and largest
        stats_result = await self.session.execute(
            select(
                func.avg(Transaction.amount),
                func.max(Transaction.amount)
            ).where(date_filter)
        )
        stats = stats_result.one()
        average_amount = float(stats[0] or 0)
        largest_transaction = stats[1] or 0
        
        # By type
        type_result = await self.session.execute(
            select(
                Transaction.transaction_type,
                func.count(Transaction.id)
            )
            .where(date_filter)
            .group_by(Transaction.transaction_type)
        )
        transaction_by_type = {row[0].value: row[1] for row in type_result.all()}
        
        # By status
        status_result = await self.session.execute(
            select(
                Transaction.status,
                func.count(Transaction.id)
            )
            .where(
                and_(
                    Transaction.account_id.in_(account_ids),
                    Transaction.created_at >= start_date,
                    Transaction.created_at <= end_date
                )
            )
            .group_by(Transaction.status)
        )
        transaction_by_status = {row[0].value: row[1] for row in status_result.all()}
        
        # Daily volume (simplified - would use date trunc in production)
        daily_volume: List[dict[str, Any]] = []
        
        return TransactionAnalytics(
            total_transactions=total_transactions,
            total_credits=total_credits,
            total_debits=total_debits,
            net_flow=total_credits - total_debits,
            average_transaction_amount=average_amount,
            largest_transaction=largest_transaction,
            transaction_by_type=transaction_by_type,
            transaction_by_status=transaction_by_status,
            daily_volume=daily_volume
        )
    
    async def get_flagged_transactions(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> TransactionListResponse:
        """Get flagged/suspicious transactions (admin)"""
        query = (
            select(Transaction)
            .where(
                or_(
                    Transaction.is_suspicious == True,
                    Transaction.status == TransactionStatus.FLAGGED,
                    Transaction.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL])
                )
            )
            .order_by(Transaction.created_at.desc())
        )
        
        count_query = select(func.count(Transaction.id)).where(
            or_(
                Transaction.is_suspicious == True,
                Transaction.status == TransactionStatus.FLAGGED,
                Transaction.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL])
            )
        )
        
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        transactions = result.scalars().all()
        
        return TransactionListResponse(
            transactions=[TransactionResponse.model_validate(t) for t in transactions],
            total=total,
            page=page,
            page_size=page_size
        )
    
    async def review_transaction(
        self,
        transaction_id: UUID,
        action: str,
        reviewer_id: UUID,
        notes: str
    ) -> Tuple[bool, Optional[str]]:
        """Review and take action on flagged transaction"""
        transaction = await self.get_transaction(transaction_id)
        
        if not transaction:
            return False, "Transaction not found"
        
        if action == "approve":
            transaction.status = TransactionStatus.COMPLETED
            transaction.is_suspicious = False
        elif action == "reject":
            transaction.status = TransactionStatus.CANCELLED
            # Reverse the transaction if it was processed
            if transaction.status == TransactionStatus.PROCESSING:
                # Would trigger reversal logic here
                pass
        elif action == "escalate":
            transaction.status = TransactionStatus.ON_HOLD
        
        transaction.reviewed_by = reviewer_id
        transaction.reviewed_at = datetime.utcnow()
        transaction.review_notes = notes
        
        await self.session.commit()
        
        logger.info(
            "Transaction reviewed",
            transaction_id=str(transaction_id),
            action=action,
            reviewer_id=str(reviewer_id)
        )
        
        return True, None
    
    async def create_dispute(
        self,
        user_id: UUID,
        data: DisputeRequest
    ) -> Tuple[Optional[DisputeResponse], Optional[str]]:
        """Create a transaction dispute"""
        transaction = await self.get_transaction(data.transaction_id)
        
        if not transaction:
            return None, "Transaction not found"
        
        # Verify user owns the transaction
        account_result = await self.session.execute(
            select(Account).where(Account.id == transaction.account_id)
        )
        account = account_result.scalar_one_or_none()
        
        if not account or account.user_id != user_id:
            return None, "Not authorized"
        
        # In production, would create a dispute record
        # For now, flag the transaction
        transaction.status = TransactionStatus.FLAGGED
        transaction.is_suspicious = True
        transaction.review_notes = f"DISPUTE: {data.reason} - {data.description}"
        
        await self.session.commit()
        
        logger.info(
            "Dispute created",
            transaction_id=str(data.transaction_id),
            user_id=str(user_id),
            reason=data.reason
        )
        
        return DisputeResponse(
            id=transaction.id,  # Would be dispute ID in production
            transaction_id=transaction.id,
            status="under_review",
            reason=data.reason,
            description=data.description,
            estimated_resolution_date=datetime.utcnow() + timedelta(days=10),
            created_at=datetime.utcnow()
        ), None
    
    async def get_recent_activity(
        self,
        user_id: UUID,
        limit: int = 10
    ) -> List[Transaction]:
        """Get recent transaction activity for user"""
        accounts_result = await self.session.execute(
            select(Account.id).where(Account.user_id == user_id)
        )
        account_ids = [row[0] for row in accounts_result.all()]
        
        if not account_ids:
            return []
        
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.account_id.in_(account_ids))
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

