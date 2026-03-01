"""
Order Service
Manages BNPL orders and installments
"""
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Tuple, Optional
from uuid import UUID, uuid4
import structlog

from app.config import settings
from app.models.schemas import (
    OrderCreateRequest, OrderResponse, OrderStatus,
    InstallmentSchedule, InstallmentStatus, PaymentResponse
)
from app.services.credit_scoring import credit_scoring_service

logger = structlog.get_logger(__name__)


class OrderService:
    """BNPL order management"""
    
    def __init__(self):
        # In-memory storage (use database in production)
        self._orders: Dict[str, Dict[str, Any]] = {}
        self._merchants: Dict[str, Dict[str, Any]] = self._load_mock_merchants()
    
    def _load_mock_merchants(self) -> Dict[str, Dict[str, Any]]:
        """Load mock merchant data"""
        merchant1_id = str(uuid4())
        merchant2_id = str(uuid4())
        merchant3_id = str(uuid4())
        
        return {
            merchant1_id: {
                "id": UUID(merchant1_id),
                "name": "ElectroMart",
                "category": "electronics",
                "logo_url": "/logos/electromart.png",
                "commission_rate": 0.025,
                "is_active": True,
                "max_order_amount": 500000,
                "allowed_installments": [3, 4, 6, 12]
            },
            merchant2_id: {
                "id": UUID(merchant2_id),
                "name": "FashionHub",
                "category": "fashion",
                "logo_url": "/logos/fashionhub.png",
                "commission_rate": 0.03,
                "is_active": True,
                "max_order_amount": 200000,
                "allowed_installments": [3, 4, 6]
            },
            merchant3_id: {
                "id": UUID(merchant3_id),
                "name": "HomeStyle",
                "category": "home",
                "logo_url": "/logos/homestyle.png",
                "commission_rate": 0.02,
                "is_active": True,
                "max_order_amount": 1000000,
                "allowed_installments": [3, 4, 6, 12]
            }
        }
    
    def _generate_order_number(self) -> str:
        """Generate unique order number"""
        import random
        import string
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"BNPL-{timestamp}-{suffix}"
    
    def _calculate_installment_schedule(
        self,
        total_amount: int,
        num_installments: int,
        start_date: date
    ) -> List[InstallmentSchedule]:
        """Calculate installment payment schedule"""
        schedules = []
        
        # Calculate installment amount (round up for first installments)
        base_amount = total_amount // num_installments
        remainder = total_amount % num_installments
        
        for i in range(num_installments):
            # Add remainder to first installments
            installment_amount = base_amount + (1 if i < remainder else 0)
            
            # Due date: first payment immediately, then monthly
            if i == 0:
                due_date = start_date
            else:
                due_date = start_date + timedelta(days=30 * i)
            
            schedules.append(InstallmentSchedule(
                installment_number=i + 1,
                due_date=due_date,
                amount=installment_amount,
                principal=installment_amount,  # 0% interest for demo
                interest=0,
                status=InstallmentStatus.SCHEDULED if i > 0 else InstallmentStatus.PENDING
            ))
        
        return schedules
    
    async def create_order(
        self,
        request: OrderCreateRequest
    ) -> Tuple[Optional[OrderResponse], Optional[str]]:
        """Create a new BNPL order"""
        
        # Validate merchant
        merchant = self._merchants.get(str(request.merchant_id))
        if not merchant:
            return None, "Merchant not found"
        
        if not merchant["is_active"]:
            return None, "Merchant is not active"
        
        if request.amount > merchant["max_order_amount"]:
            return None, f"Amount exceeds merchant limit (${merchant['max_order_amount']/100:.2f})"
        
        if request.installments not in merchant["allowed_installments"]:
            return None, f"Invalid installment option. Allowed: {merchant['allowed_installments']}"
        
        # Check eligibility
        eligibility = await credit_scoring_service.check_eligibility(
            request.user_id,
            request.amount
        )
        
        if not eligibility.is_approved:
            return None, "; ".join(eligibility.rejection_reasons)
        
        # Create order
        order_id = uuid4()
        order_number = self._generate_order_number()
        
        # Calculate installments
        today = date.today()
        schedule = self._calculate_installment_schedule(
            request.amount,
            request.installments,
            today
        )
        
        installment_amount = request.amount // request.installments
        
        order_data = {
            "id": order_id,
            "user_id": request.user_id,
            "merchant_id": request.merchant_id,
            "merchant_name": merchant["name"],
            "order_number": order_number,
            "total_amount": request.amount,
            "installment_amount": installment_amount,
            "installments_count": request.installments,
            "paid_installments": 0,
            "remaining_amount": request.amount,
            "status": OrderStatus.APPROVED,
            "schedule": schedule,
            "items": request.items,
            "shipping_address": request.shipping_address,
            "created_at": datetime.utcnow(),
            "next_payment_date": today
        }
        
        self._orders[str(order_id)] = order_data
        
        logger.info(
            "BNPL order created",
            order_id=str(order_id),
            order_number=order_number,
            user_id=str(request.user_id),
            amount=request.amount,
            installments=request.installments
        )
        
        return OrderResponse(
            id=order_id,
            user_id=request.user_id,
            merchant_id=request.merchant_id,
            merchant_name=merchant["name"],
            order_number=order_number,
            total_amount=request.amount,
            installment_amount=installment_amount,
            installments_count=request.installments,
            paid_installments=0,
            remaining_amount=request.amount,
            status=OrderStatus.APPROVED,
            schedule=schedule,
            items=request.items,
            created_at=datetime.utcnow(),
            next_payment_date=today
        ), None
    
    async def get_order(self, order_id: UUID) -> Optional[OrderResponse]:
        """Get order by ID"""
        order_data = self._orders.get(str(order_id))
        if not order_data:
            return None
        
        return OrderResponse(**order_data)
    
    async def get_user_orders(
        self,
        user_id: UUID,
        status: Optional[OrderStatus] = None
    ) -> List[OrderResponse]:
        """Get all orders for a user"""
        orders = []
        
        for order_data in self._orders.values():
            if order_data["user_id"] == user_id:
                if status is None or order_data["status"] == status:
                    orders.append(OrderResponse(**order_data))
        
        return sorted(orders, key=lambda x: x.created_at, reverse=True)
    
    async def make_payment(
        self,
        order_id: UUID,
        amount: int
    ) -> Tuple[Optional[PaymentResponse], Optional[str]]:
        """Make an installment payment"""
        order_data = self._orders.get(str(order_id))
        
        if not order_data:
            return None, "Order not found"
        
        if order_data["status"] not in [OrderStatus.APPROVED, OrderStatus.ACTIVE]:
            return None, f"Order is not active (status: {order_data['status'].value})"
        
        # Find next unpaid installment
        schedule = order_data["schedule"]
        next_installment = None
        installment_number = 0
        
        for i, inst in enumerate(schedule):
            if inst.status in [InstallmentStatus.SCHEDULED, InstallmentStatus.PENDING, InstallmentStatus.OVERDUE]:
                next_installment = inst
                installment_number = i + 1
                break
        
        if not next_installment:
            return None, "No pending installments"
        
        if amount < next_installment.amount:
            return None, f"Amount insufficient. Required: ${next_installment.amount/100:.2f}"
        
        # Update installment
        schedule[installment_number - 1] = InstallmentSchedule(
            installment_number=installment_number,
            due_date=next_installment.due_date,
            amount=next_installment.amount,
            principal=next_installment.principal,
            interest=next_installment.interest,
            status=InstallmentStatus.PAID
        )
        
        # Update order
        order_data["paid_installments"] += 1
        order_data["remaining_amount"] -= next_installment.amount
        order_data["schedule"] = schedule
        
        if order_data["paid_installments"] >= order_data["installments_count"]:
            order_data["status"] = OrderStatus.COMPLETED
            order_data["next_payment_date"] = None
        else:
            order_data["status"] = OrderStatus.ACTIVE
            # Find next payment date
            for inst in schedule:
                if inst.status != InstallmentStatus.PAID:
                    order_data["next_payment_date"] = inst.due_date
                    break
        
        logger.info(
            "Payment processed",
            order_id=str(order_id),
            installment=installment_number,
            amount=amount
        )
        
        return PaymentResponse(
            payment_id=uuid4(),
            order_id=order_id,
            amount=next_installment.amount,
            installment_number=installment_number,
            status="success",
            paid_at=datetime.utcnow(),
            remaining_installments=order_data["installments_count"] - order_data["paid_installments"],
            remaining_amount=order_data["remaining_amount"]
        ), None
    
    async def get_merchants(self) -> List[Dict[str, Any]]:
        """Get all active merchants"""
        return [m for m in self._merchants.values() if m["is_active"]]
    
    async def get_merchant(self, merchant_id: UUID) -> Optional[Dict[str, Any]]:
        """Get merchant by ID"""
        return self._merchants.get(str(merchant_id))


# Global instance
order_service = OrderService()

