"""
User Service
Handles user profile management and KYC
"""
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import structlog

from app.models.user import User, UserProfile, UserStatus, UserRole
from app.schemas.user import (
    UserResponse, UserProfileUpdate, UserListResponse,
    KYCSubmitRequest, KYCStatusResponse
)

logger = structlog.get_logger(__name__)


class UserService:
    """User management service"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user(self, user_id: UUID) -> Optional[User]:
        """Get user by ID with profile"""
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_users(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[UserStatus] = None,
        role: Optional[UserRole] = None,
        search: Optional[str] = None
    ) -> UserListResponse:
        """Get paginated list of users"""
        query = select(User).options(selectinload(User.profile))
        count_query = select(func.count(User.id))
        
        # Apply filters
        if status:
            query = query.where(User.status == status)
            count_query = count_query.where(User.status == status)
        
        if role:
            query = query.where(User.role == role)
            count_query = count_query.where(User.role == role)
        
        if search:
            search_filter = User.email.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(User.created_at.desc())
        
        result = await self.session.execute(query)
        users = result.scalars().all()
        
        return UserListResponse(
            users=[UserResponse.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size
        )
    
    async def update_profile(
        self,
        user_id: UUID,
        update_data: UserProfileUpdate
    ) -> Tuple[Optional[UserProfile], Optional[str]]:
        """Update user profile"""
        user = await self.get_user(user_id)
        
        if not user:
            return None, "User not found"
        
        if not user.profile:
            return None, "Profile not found"
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(user.profile, field, value)
        
        user.profile.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(user.profile)
        
        logger.info("Profile updated", user_id=str(user_id))
        
        return user.profile, None
    
    async def update_status(
        self,
        user_id: UUID,
        status: UserStatus,
        reason: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Update user account status"""
        user = await self.get_user(user_id)
        
        if not user:
            return False, "User not found"
        
        old_status = user.status
        user.status = status
        user.updated_at = datetime.utcnow()
        
        await self.session.commit()
        
        logger.info(
            "User status updated",
            user_id=str(user_id),
            old_status=old_status.value,
            new_status=status.value,
            reason=reason
        )
        
        return True, None
    
    async def verify_email(self, user_id: UUID) -> Tuple[bool, Optional[str]]:
        """Mark email as verified"""
        user = await self.get_user(user_id)
        
        if not user:
            return False, "User not found"
        
        if user.is_email_verified:
            return False, "Email already verified"
        
        user.is_email_verified = True
        
        # Activate account if pending
        if user.status == UserStatus.PENDING:
            user.status = UserStatus.ACTIVE
        
        await self.session.commit()
        
        logger.info("Email verified", user_id=str(user_id))
        
        return True, None
    
    async def verify_phone(self, user_id: UUID) -> Tuple[bool, Optional[str]]:
        """Mark phone as verified"""
        user = await self.get_user(user_id)
        
        if not user:
            return False, "User not found"
        
        if user.is_phone_verified:
            return False, "Phone already verified"
        
        user.is_phone_verified = True
        await self.session.commit()
        
        logger.info("Phone verified", user_id=str(user_id))
        
        return True, None
    
    async def submit_kyc(
        self,
        user_id: UUID,
        kyc_data: KYCSubmitRequest
    ) -> Tuple[Optional[KYCStatusResponse], Optional[str]]:
        """Submit KYC documents"""
        user = await self.get_user(user_id)
        
        if not user or not user.profile:
            return None, "User not found"
        
        # Update profile with KYC data
        user.profile.id_type = kyc_data.id_type
        user.profile.id_number = kyc_data.id_number
        user.profile.id_expiry = kyc_data.id_expiry
        
        # In production, would store document URLs and trigger verification
        # For now, simulate KYC submission
        
        user.kyc_level = 1  # Basic KYC submitted
        await self.session.commit()
        
        logger.info("KYC submitted", user_id=str(user_id), level=1)
        
        # TODO: Trigger async KYC verification process
        
        return KYCStatusResponse(
            kyc_level=1,
            status="pending_review",
            documents_submitted=[kyc_data.id_type, "selfie"],
            pending_documents=[]
        ), None
    
    async def get_kyc_status(self, user_id: UUID) -> Optional[KYCStatusResponse]:
        """Get KYC verification status"""
        user = await self.get_user(user_id)
        
        if not user:
            return None
        
        status_map = {
            0: "not_started",
            1: "pending_review",
            2: "verified_basic",
            3: "verified_full"
        }
        
        documents_required = ["government_id", "selfie", "proof_of_address"]
        documents_submitted = []
        
        if user.profile and user.profile.id_type:
            documents_submitted.append(user.profile.id_type)
        
        return KYCStatusResponse(
            kyc_level=user.kyc_level,
            status=status_map.get(user.kyc_level, "unknown"),
            verified_at=user.kyc_verified_at,
            documents_submitted=documents_submitted,
            pending_documents=[d for d in documents_required if d not in documents_submitted]
        )
    
    async def approve_kyc(
        self,
        user_id: UUID,
        level: int,
        admin_id: UUID
    ) -> Tuple[bool, Optional[str]]:
        """Approve KYC (admin only)"""
        user = await self.get_user(user_id)
        
        if not user:
            return False, "User not found"
        
        if level not in [1, 2, 3]:
            return False, "Invalid KYC level"
        
        user.kyc_level = level
        user.kyc_verified_at = datetime.utcnow()
        
        await self.session.commit()
        
        logger.info(
            "KYC approved",
            user_id=str(user_id),
            level=level,
            approved_by=str(admin_id)
        )
        
        return True, None
    
    async def search_users(
        self,
        query: str,
        limit: int = 20
    ) -> List[User]:
        """Search users by email or phone"""
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(
                (User.email.ilike(f"%{query}%")) |
                (User.phone.ilike(f"%{query}%"))
            )
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def delete_user(self, user_id: UUID) -> Tuple[bool, Optional[str]]:
        """Soft delete user account"""
        user = await self.get_user(user_id)
        
        if not user:
            return False, "User not found"
        
        user.status = UserStatus.CLOSED
        user.email = f"deleted_{user_id}@deleted.local"
        user.phone = None
        
        await self.session.commit()
        
        logger.info("User deleted", user_id=str(user_id))
        
        return True, None

