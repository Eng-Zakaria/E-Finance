"""
Credit Scoring Service
Evaluates user creditworthiness for BNPL
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
from uuid import UUID
import numpy as np
import structlog

from app.config import settings
from app.models.schemas import CreditCheckResponse, CreditScoreFactors

logger = structlog.get_logger(__name__)


class CreditScoringService:
    """Credit scoring and eligibility assessment"""
    
    # Score weights
    WEIGHTS = {
        "payment_history": 0.35,
        "credit_utilization": 0.30,
        "account_age": 0.15,
        "order_history": 0.20
    }
    
    def __init__(self):
        # In production, would load ML model
        pass
    
    async def calculate_credit_score(
        self,
        user_id: UUID,
        user_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, CreditScoreFactors]:
        """
        Calculate credit score for a user
        Returns score (300-850) and factor breakdown
        """
        if user_data is None:
            user_data = await self._get_user_data(user_id)
        
        # Calculate individual factors
        payment_history_score = self._calculate_payment_history_score(user_data)
        credit_utilization_score = self._calculate_utilization_score(user_data)
        account_age_score = self._calculate_account_age_score(user_data)
        order_history_score = self._calculate_order_history_score(user_data)
        
        # Weighted average
        weighted_score = (
            payment_history_score * self.WEIGHTS["payment_history"] +
            credit_utilization_score * self.WEIGHTS["credit_utilization"] +
            account_age_score * self.WEIGHTS["account_age"] +
            order_history_score * self.WEIGHTS["order_history"]
        )
        
        # Convert to 300-850 scale
        final_score = int(300 + (weighted_score / 100) * 550)
        final_score = max(settings.MIN_CREDIT_SCORE, min(settings.MAX_CREDIT_SCORE, final_score))
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            payment_history_score,
            credit_utilization_score,
            account_age_score,
            order_history_score
        )
        
        factors = CreditScoreFactors(
            payment_history=payment_history_score,
            credit_utilization=credit_utilization_score,
            account_age=account_age_score,
            order_history=order_history_score,
            overall_score=final_score,
            recommendations=recommendations
        )
        
        logger.info(
            "Credit score calculated",
            user_id=str(user_id),
            score=final_score
        )
        
        return final_score, factors
    
    async def _get_user_data(self, user_id: UUID) -> Dict[str, Any]:
        """Get user data for scoring (mock implementation)"""
        # In production, would fetch from database and core banking API
        return {
            "account_created_at": datetime.utcnow() - timedelta(days=180),
            "total_orders": 5,
            "completed_orders": 4,
            "defaulted_orders": 0,
            "on_time_payments": 12,
            "late_payments": 1,
            "total_payments": 13,
            "current_credit_used": 30000,  # $300
            "credit_limit": 100000,  # $1000
            "avg_order_amount": 15000,  # $150
            "kyc_verified": True
        }
    
    def _calculate_payment_history_score(self, data: Dict[str, Any]) -> int:
        """Calculate score based on payment history"""
        total_payments = data.get("total_payments", 0)
        
        if total_payments == 0:
            return 50  # Neutral for new users
        
        on_time = data.get("on_time_payments", 0)
        late = data.get("late_payments", 0)
        
        on_time_rate = on_time / total_payments
        
        # Penalty for late payments
        late_penalty = min(late * 10, 50)
        
        score = int(on_time_rate * 100) - late_penalty
        
        return max(0, min(100, score))
    
    def _calculate_utilization_score(self, data: Dict[str, Any]) -> int:
        """Calculate score based on credit utilization"""
        credit_limit = data.get("credit_limit", 1)
        used = data.get("current_credit_used", 0)
        
        if credit_limit == 0:
            return 50
        
        utilization = used / credit_limit
        
        # Optimal utilization is 10-30%
        if utilization < 0.1:
            score = 80  # Too low utilization
        elif utilization <= 0.3:
            score = 100  # Optimal
        elif utilization <= 0.5:
            score = 80
        elif utilization <= 0.7:
            score = 60
        elif utilization <= 0.9:
            score = 40
        else:
            score = 20  # High utilization
        
        return score
    
    def _calculate_account_age_score(self, data: Dict[str, Any]) -> int:
        """Calculate score based on account age"""
        created_at = data.get("account_created_at", datetime.utcnow())
        age_days = (datetime.utcnow() - created_at).days
        
        if age_days < 30:
            return 30
        elif age_days < 90:
            return 50
        elif age_days < 180:
            return 70
        elif age_days < 365:
            return 85
        else:
            return 100
    
    def _calculate_order_history_score(self, data: Dict[str, Any]) -> int:
        """Calculate score based on order history"""
        total_orders = data.get("total_orders", 0)
        completed = data.get("completed_orders", 0)
        defaulted = data.get("defaulted_orders", 0)
        
        if total_orders == 0:
            return 50  # Neutral for new users
        
        completion_rate = completed / total_orders
        default_penalty = defaulted * 25
        
        score = int(completion_rate * 100) - default_penalty
        
        return max(0, min(100, score))
    
    def _generate_recommendations(
        self,
        payment_history: int,
        utilization: int,
        account_age: int,
        order_history: int
    ) -> List[str]:
        """Generate recommendations to improve credit score"""
        recommendations = []
        
        if payment_history < 70:
            recommendations.append("Pay all installments on time to improve payment history")
        
        if utilization < 50:
            recommendations.append("Keep credit utilization below 30% of your limit")
        
        if account_age < 50:
            recommendations.append("Account age will naturally improve over time")
        
        if order_history < 70:
            recommendations.append("Complete your existing orders to build positive history")
        
        if len(recommendations) == 0:
            recommendations.append("Your credit profile is excellent! Keep it up.")
        
        return recommendations
    
    async def check_eligibility(
        self,
        user_id: UUID,
        requested_amount: int
    ) -> CreditCheckResponse:
        """Check if user is eligible for BNPL purchase"""
        
        # Calculate credit score
        score, factors = await self.calculate_credit_score(user_id)
        
        # Get user data
        user_data = await self._get_user_data(user_id)
        
        # Calculate available credit
        credit_limit = user_data.get("credit_limit", settings.DEFAULT_CREDIT_LIMIT)
        used_credit = user_data.get("current_credit_used", 0)
        available_credit = credit_limit - used_credit
        
        # Check approval
        rejection_reasons = []
        is_approved = True
        
        if score < settings.MIN_APPROVAL_SCORE:
            is_approved = False
            rejection_reasons.append(f"Credit score ({score}) below minimum required ({settings.MIN_APPROVAL_SCORE})")
        
        if requested_amount > available_credit:
            is_approved = False
            rejection_reasons.append(f"Requested amount exceeds available credit (${available_credit/100:.2f})")
        
        if requested_amount < settings.MIN_PURCHASE_AMOUNT:
            is_approved = False
            rejection_reasons.append(f"Amount below minimum (${settings.MIN_PURCHASE_AMOUNT/100:.2f})")
        
        if requested_amount > settings.MAX_PURCHASE_AMOUNT:
            is_approved = False
            rejection_reasons.append(f"Amount exceeds maximum (${settings.MAX_PURCHASE_AMOUNT/100:.2f})")
        
        # Determine max installments based on score
        if score >= 750:
            max_installments = 12
        elif score >= 650:
            max_installments = 6
        elif score >= 550:
            max_installments = 4
        else:
            max_installments = 3
        
        logger.info(
            "Eligibility checked",
            user_id=str(user_id),
            amount=requested_amount,
            approved=is_approved,
            score=score
        )
        
        return CreditCheckResponse(
            user_id=user_id,
            credit_score=score,
            credit_limit=credit_limit,
            available_credit=available_credit,
            is_approved=is_approved,
            max_installments=max_installments,
            rejection_reasons=rejection_reasons,
            checked_at=datetime.utcnow()
        )
    
    async def calculate_credit_limit(self, user_id: UUID) -> int:
        """Calculate appropriate credit limit for user"""
        score, _ = await self.calculate_credit_score(user_id)
        
        # Base limit based on score
        if score >= 800:
            base_limit = settings.MAX_CREDIT_LIMIT
        elif score >= 750:
            base_limit = 500000  # $5000
        elif score >= 700:
            base_limit = 300000  # $3000
        elif score >= 650:
            base_limit = 200000  # $2000
        elif score >= 600:
            base_limit = 100000  # $1000
        elif score >= 550:
            base_limit = 50000  # $500
        else:
            base_limit = 25000  # $250
        
        return base_limit


# Global instance
credit_scoring_service = CreditScoringService()

