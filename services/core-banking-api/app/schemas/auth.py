"""
Authentication Schemas
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    device_id: Optional[str] = None
    device_type: Optional[str] = None


class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    requires_2fa: bool = False


class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        # Remove any non-digit characters
        digits = re.sub(r'\D', '', v)
        if len(digits) < 10:
            raise ValueError('Invalid phone number')
        return v


class RegisterResponse(BaseModel):
    """Registration response"""
    user_id: str
    email: str
    message: str = "Registration successful. Please verify your email."


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    """Email verification request"""
    token: str


class ResetPasswordRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class ConfirmResetPasswordRequest(BaseModel):
    """Confirm password reset"""
    token: str
    new_password: str = Field(..., min_length=8)


class Change2FARequest(BaseModel):
    """Enable/disable 2FA"""
    enable: bool
    totp_code: Optional[str] = None


class Verify2FARequest(BaseModel):
    """2FA verification during login"""
    user_id: str
    totp_code: str = Field(..., min_length=6, max_length=6)


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # user_id
    exp: int
    iat: int
    type: str  # access or refresh
    role: str

