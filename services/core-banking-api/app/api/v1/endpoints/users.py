"""
User Endpoints
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.user_service import UserService
from app.schemas.user import (
    UserResponse, UserProfileUpdate, UserListResponse,
    KYCSubmitRequest, KYCStatusResponse
)
from app.api.v1.deps import get_current_user, get_current_admin
from app.models.user import User, UserStatus

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get current user's profile.
    """
    user_service = UserService(session)
    user = await user_service.get_user(current_user.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Update current user's profile.
    """
    user_service = UserService(session)
    profile, error = await user_service.update_profile(current_user.id, data)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    user = await user_service.get_user(current_user.id)
    return UserResponse.model_validate(user)


@router.post("/me/kyc", response_model=KYCStatusResponse)
async def submit_kyc(
    data: KYCSubmitRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Submit KYC documents for verification.
    """
    user_service = UserService(session)
    response, error = await user_service.submit_kyc(current_user.id, data)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return response


@router.get("/me/kyc", response_model=KYCStatusResponse)
async def get_kyc_status(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get current KYC verification status.
    """
    user_service = UserService(session)
    status_response = await user_service.get_kyc_status(current_user.id)
    
    if not status_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return status_response


# Admin endpoints
@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[UserStatus] = None,
    search: Optional[str] = None,
    admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    List all users (admin only).
    """
    user_service = UserService(session)
    return await user_service.get_users(
        page=page,
        page_size=page_size,
        status=status_filter,
        search=search
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Get user by ID (admin only).
    """
    user_service = UserService(session)
    user = await user_service.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.patch("/{user_id}/status", response_model=dict)
async def update_user_status(
    user_id: UUID,
    new_status: UserStatus,
    reason: Optional[str] = None,
    admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Update user account status (admin only).
    """
    user_service = UserService(session)
    success, error = await user_service.update_status(user_id, new_status, reason)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"message": f"User status updated to {new_status.value}"}


@router.post("/{user_id}/kyc/approve", response_model=dict)
async def approve_user_kyc(
    user_id: UUID,
    level: int = Query(..., ge=1, le=3),
    admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Approve user KYC (admin only).
    """
    user_service = UserService(session)
    success, error = await user_service.approve_kyc(user_id, level, admin.id)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"message": f"KYC approved at level {level}"}

