"""
User Schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

from app.models.user import UserRole, UserStatus


class UserProfileBase(BaseModel):
    """User profile base schema"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    nationality: Optional[str] = Field(None, max_length=3)


class UserProfileCreate(UserProfileBase):
    """Create user profile"""
    pass


class UserProfileUpdate(BaseModel):
    """Update user profile"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    nationality: Optional[str] = Field(None, max_length=3)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=3)
    
    # Employment
    occupation: Optional[str] = Field(None, max_length=100)
    employer: Optional[str] = Field(None, max_length=255)
    annual_income: Optional[int] = None
    source_of_funds: Optional[str] = Field(None, max_length=100)


class UserProfileResponse(UserProfileBase):
    """User profile response"""
    id: UUID
    user_id: UUID
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    """User base schema"""
    email: EmailStr
    phone: Optional[str] = None


class UserCreate(UserBase):
    """Create user schema"""
    password: str = Field(..., min_length=8)
    profile: UserProfileCreate


class UserResponse(UserBase):
    """User response schema"""
    id: UUID
    role: UserRole
    status: UserStatus
    is_email_verified: bool
    is_phone_verified: bool
    is_2fa_enabled: bool
    kyc_level: int
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    profile: Optional[UserProfileResponse] = None
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """List of users response"""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int


class UserUpdateRequest(BaseModel):
    """Update user request"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class KYCSubmitRequest(BaseModel):
    """KYC document submission"""
    id_type: str = Field(..., description="Type of ID (passport, national_id, drivers_license)")
    id_number: str
    id_expiry: datetime
    id_front_url: str = Field(..., description="URL of front of ID document")
    id_back_url: Optional[str] = Field(None, description="URL of back of ID document")
    selfie_url: str = Field(..., description="URL of selfie with ID")
    proof_of_address_url: Optional[str] = None


class KYCStatusResponse(BaseModel):
    """KYC status response"""
    kyc_level: int
    status: str
    verified_at: Optional[datetime] = None
    documents_submitted: List[str] = []
    pending_documents: List[str] = []
    rejection_reason: Optional[str] = None

