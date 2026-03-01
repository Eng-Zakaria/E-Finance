"""
Order Endpoints
"""
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Query

from app.models.schemas import (
    OrderCreateRequest, OrderResponse, OrderStatus,
    PaymentRequest, PaymentResponse
)
from app.services.order_service import order_service

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(request: OrderCreateRequest):
    """
    Create a new BNPL order.
    """
    order, error = await order_service.create_order(request)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return order


@router.get("/user/{user_id}", response_model=List[OrderResponse])
async def get_user_orders(
    user_id: UUID,
    status_filter: Optional[OrderStatus] = None
):
    """
    Get all orders for a user.
    """
    return await order_service.get_user_orders(user_id, status_filter)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: UUID):
    """
    Get order details.
    """
    order = await order_service.get_order(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@router.post("/{order_id}/pay", response_model=PaymentResponse)
async def make_payment(order_id: UUID, request: PaymentRequest):
    """
    Make an installment payment.
    """
    result, error = await order_service.make_payment(order_id, request.amount)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return result


@router.get("/{order_id}/schedule", response_model=list)
async def get_payment_schedule(order_id: UUID):
    """
    Get payment schedule for an order.
    """
    order = await order_service.get_order(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order.schedule


@router.get("/upcoming/{user_id}", response_model=dict)
async def get_upcoming_payments(user_id: UUID):
    """
    Get upcoming payments for a user.
    """
    orders = await order_service.get_user_orders(user_id)
    
    upcoming = []
    total_due = 0
    
    for order in orders:
        if order.status in [OrderStatus.APPROVED, OrderStatus.ACTIVE]:
            for inst in order.schedule:
                if inst.status != "paid":
                    upcoming.append({
                        "order_id": str(order.id),
                        "order_number": order.order_number,
                        "merchant": order.merchant_name,
                        "installment_number": inst.installment_number,
                        "amount": inst.amount,
                        "due_date": inst.due_date.isoformat(),
                        "status": inst.status
                    })
                    total_due += inst.amount
                    break  # Only next payment per order
    
    return {
        "upcoming_payments": sorted(upcoming, key=lambda x: x["due_date"]),
        "total_due": total_due,
        "count": len(upcoming)
    }

