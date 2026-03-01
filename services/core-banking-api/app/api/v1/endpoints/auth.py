"""
Authentication Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.auth_service import AuthService
from app.schemas.auth import (
    LoginRequest, LoginResponse, RegisterRequest, RegisterResponse,
    RefreshTokenRequest, Verify2FARequest
)
from app.api.v1.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Authenticate user with email and password.
    Returns JWT tokens on success.
    """
    auth_service = AuthService(session)
    response, error = await auth_service.login(request)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error,
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return response


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Register a new user account.
    """
    auth_service = AuthService(session)
    response, error = await auth_service.register(request)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return response


@router.post("/refresh", response_model=dict)
async def refresh_token(
    request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Refresh access token using refresh token.
    """
    auth_service = AuthService(session)
    access_token, error = await auth_service.refresh_access_token(request)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/verify-2fa", response_model=LoginResponse)
async def verify_2fa(
    request: Verify2FARequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Verify 2FA code to complete login.
    """
    auth_service = AuthService(session)
    response, error = await auth_service.verify_2fa(request.user_id, request.totp_code)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )
    
    return response


@router.post("/enable-2fa", response_model=dict)
async def enable_2fa(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Enable 2FA for current user. Returns secret and QR code URI.
    """
    auth_service = AuthService(session)
    result, error = await auth_service.enable_2fa(current_user.id)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return result


@router.post("/confirm-2fa", response_model=dict)
async def confirm_2fa(
    totp_code: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Confirm 2FA setup by providing a valid TOTP code.
    """
    auth_service = AuthService(session)
    success, error = await auth_service.confirm_2fa(current_user.id, totp_code)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"message": "2FA enabled successfully"}


@router.post("/disable-2fa", response_model=dict)
async def disable_2fa(
    totp_code: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Disable 2FA for current user.
    """
    auth_service = AuthService(session)
    success, error = await auth_service.disable_2fa(current_user.id, totp_code)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"message": "2FA disabled successfully"}


@router.post("/logout", response_model=dict)
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout current user (invalidate tokens on client side).
    """
    # In production, would blacklist the token
    return {"message": "Logged out successfully"}

