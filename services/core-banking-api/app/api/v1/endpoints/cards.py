"""
Card Endpoints
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.card_service import CardService
from app.schemas.card import (
    CardCreate, CardResponse, CardListResponse,
    CardActivateRequest, CardSetPinRequest,
    CardControlsUpdate, CardLimitsUpdate, VirtualCardCreate
)
from app.api.v1.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_card(
    data: CardCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new debit/credit card.
    Returns full card details (shown only once).
    """
    card_service = CardService(session)
    result, error = await card_service.create_card(current_user.id, data)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return result


@router.post("/virtual", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_virtual_card(
    data: VirtualCardCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a virtual card for online transactions.
    """
    card_service = CardService(session)
    result, error = await card_service.create_virtual_card(current_user.id, data)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return result


@router.get("/", response_model=CardListResponse)
async def list_cards(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all cards for current user.
    """
    card_service = CardService(session)
    return await card_service.get_user_cards(current_user.id)


@router.get("/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get card details.
    """
    card_service = CardService(session)
    card = await card_service.get_card(card_id)
    
    if not card or card.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    return CardResponse.model_validate(card)


@router.post("/{card_id}/activate", response_model=dict)
async def activate_card(
    card_id: UUID,
    data: CardActivateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Activate a physical card.
    """
    card_service = CardService(session)
    success, error = await card_service.activate_card(
        card_id,
        current_user.id,
        data.last_four_digits,
        data.cvv
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"message": "Card activated successfully"}


@router.post("/{card_id}/pin", response_model=dict)
async def set_card_pin(
    card_id: UUID,
    data: CardSetPinRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Set or change card PIN.
    """
    if data.pin != data.confirm_pin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PINs do not match"
        )
    
    card_service = CardService(session)
    success, error = await card_service.set_pin(card_id, current_user.id, data.pin)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"message": "PIN set successfully"}


@router.patch("/{card_id}/controls", response_model=CardResponse)
async def update_card_controls(
    card_id: UUID,
    data: CardControlsUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Update card security controls.
    """
    card_service = CardService(session)
    card, error = await card_service.update_controls(card_id, current_user.id, data)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return CardResponse.model_validate(card)


@router.patch("/{card_id}/limits", response_model=CardResponse)
async def update_card_limits(
    card_id: UUID,
    data: CardLimitsUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Update card spending limits.
    """
    card_service = CardService(session)
    card, error = await card_service.update_limits(card_id, current_user.id, data)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return CardResponse.model_validate(card)


@router.post("/{card_id}/block", response_model=dict)
async def block_card(
    card_id: UUID,
    reason: str = Query(..., pattern="^(lost|stolen|suspicious|temporary)$"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Block a card.
    """
    card_service = CardService(session)
    success, error = await card_service.block_card(card_id, current_user.id, reason)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"message": "Card blocked successfully"}


@router.post("/{card_id}/unblock", response_model=dict)
async def unblock_card(
    card_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Unblock a temporarily blocked card.
    """
    card_service = CardService(session)
    success, error = await card_service.unblock_card(card_id, current_user.id)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"message": "Card unblocked successfully"}


@router.delete("/{card_id}", response_model=dict)
async def cancel_card(
    card_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Permanently cancel a card.
    """
    card_service = CardService(session)
    success, error = await card_service.cancel_card(card_id, current_user.id)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"message": "Card cancelled successfully"}

