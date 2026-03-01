"""
BNPL Service Schemas
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum
from decimal import Decimal


class BNPLStatus(str, Enum):
    """BNPL account status"""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class OrderStatus(str, Enum):
    """BNPL order status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    COMPLETED = "completed"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"


class InstallmentStatus(str, Enum):
    """Installment payment status"""
    SCHEDULED = "scheduled"
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    FAILED = "failed"


class CreditCheckRequest(BaseModel):
    """Credit check request"""
    user_id: UUID
    requested_amount: int = Field(..., gt=0, description="Amount in cents")
    purpose: Optional[str] = None


class CreditCheckResponse(BaseModel):
    """Credit check response"""
    user_id: UUID
    credit_score: int
    credit_limit: int
    available_credit: int
    is_approved: bool
    max_installments: int
    rejection_reasons: List[str] = []
    checked_at: datetime


class BNPLAccountCreate(BaseModel):
    """Create BNPL account"""
    user_id: UUID


class BNPLAccountResponse(BaseModel):
    """BNPL account response"""
    id: UUID
    user_id: UUID
    credit_limit: int
    available_credit: int
    used_credit: int
    credit_score: int
    status: BNPLStatus
    total_orders: int
    active_orders: int
    on_time_payment_rate: float
    created_at: datetime
    updated_at: datetime


class MerchantResponse(BaseModel):
    """Merchant response"""
    id: UUID
    name: str
    category: str
    logo_url: Optional[str] = None
    commission_rate: float
    is_active: bool
    max_order_amount: int
    allowed_installments: List[int]


class OrderCreateRequest(BaseModel):
    """Create BNPL order"""
    user_id: UUID
    merchant_id: UUID
    amount: int = Field(..., gt=0, description="Total amount in cents")
    installments: int = Field(..., ge=2, le=12)
    items: List[Dict[str, Any]] = []
    shipping_address: Optional[Dict[str, str]] = None


class InstallmentSchedule(BaseModel):
    """Single installment in schedule"""
    installment_number: int
    due_date: date
    amount: int
    principal: int
    interest: int
    status: InstallmentStatus


class OrderResponse(BaseModel):
    """BNPL order response"""
    id: UUID
    user_id: UUID
    merchant_id: UUID
    merchant_name: str
    order_number: str
    total_amount: int
    installment_amount: int
    installments_count: int
    paid_installments: int
    remaining_amount: int
    status: OrderStatus
    schedule: List[InstallmentSchedule]
    items: List[Dict[str, Any]]
    created_at: datetime
    next_payment_date: Optional[date] = None


class PaymentRequest(BaseModel):
    """Make installment payment"""
    order_id: UUID
    amount: int = Field(..., gt=0)
    payment_method: str = Field(default="bank_account")
    source_account_id: Optional[UUID] = None


class PaymentResponse(BaseModel):
    """Payment response"""
    payment_id: UUID
    order_id: UUID
    amount: int
    installment_number: int
    status: str
    paid_at: datetime
    remaining_installments: int
    remaining_amount: int


class EligibilityCheckRequest(BaseModel):
    """Check purchase eligibility"""
    user_id: UUID
    amount: int = Field(..., gt=0)
    merchant_id: Optional[UUID] = None


class EligibilityResponse(BaseModel):
    """Eligibility check response"""
    is_eligible: bool
    max_amount: int
    available_installment_options: List[int]
    monthly_payment_estimates: Dict[int, int]  # installments -> monthly amount
    reasons: List[str] = []


class OrderHistoryResponse(BaseModel):
    """Order history"""
    orders: List[OrderResponse]
    total_orders: int
    total_paid: int
    total_outstanding: int


class UpcomingPaymentsResponse(BaseModel):
    """Upcoming payments"""
    payments: List[Dict[str, Any]]
    total_due_this_month: int
    total_due_next_month: int


class CreditScoreFactors(BaseModel):
    """Credit score breakdown"""
    payment_history: int  # 0-100
    credit_utilization: int  # 0-100
    account_age: int  # 0-100
    order_history: int  # 0-100
    overall_score: int
    recommendations: List[str]

