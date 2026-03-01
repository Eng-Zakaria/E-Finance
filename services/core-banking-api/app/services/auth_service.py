"""
Authentication Service
Handles user authentication, JWT tokens, and security
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID
import secrets
import hashlib

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import pyotp
import structlog

from app.config import settings
from app.models.user import User, UserStatus, UserRole
from app.schemas.auth import (
    LoginRequest, LoginResponse, RegisterRequest, RegisterResponse,
    TokenPayload, RefreshTokenRequest
)
from app.database import get_redis

logger = structlog.get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(user_id: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": user_id,
            "role": role,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16),  # Unique token ID
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    @staticmethod
    def decode_token(token: str) -> Optional[TokenPayload]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return TokenPayload(**payload)
        except JWTError:
            return None
    
    @staticmethod
    def generate_totp_secret() -> str:
        """Generate TOTP secret for 2FA"""
        return pyotp.random_base32()
    
    @staticmethod
    def verify_totp(secret: str, code: str) -> bool:
        """Verify TOTP code"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code)
    
    @staticmethod
    def get_totp_uri(secret: str, email: str) -> str:
        """Get TOTP provisioning URI for QR code"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name="E-Finance")
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def authenticate(self, request: LoginRequest) -> Tuple[Optional[User], Optional[str]]:
        """
        Authenticate user with email and password
        Returns (user, error_message)
        """
        user = await self.get_user_by_email(request.email)
        
        if not user:
            logger.warning("Login attempt for non-existent user", email=request.email)
            return None, "Invalid email or password"
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            remaining = (user.locked_until - datetime.utcnow()).seconds // 60
            logger.warning("Login attempt for locked account", user_id=str(user.id))
            return None, f"Account is locked. Try again in {remaining} minutes."
        
        # Check account status
        if user.status == UserStatus.BLOCKED:
            return None, "Account has been blocked. Contact support."
        if user.status == UserStatus.CLOSED:
            return None, "Account has been closed."
        
        # Verify password
        if not self.verify_password(request.password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
                logger.warning("Account locked due to failed attempts", user_id=str(user.id))
            
            await self.session.commit()
            return None, "Invalid email or password"
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = request.device_id  # In production, extract from request
        
        await self.session.commit()
        
        return user, None
    
    async def login(self, request: LoginRequest) -> Tuple[Optional[LoginResponse], Optional[str]]:
        """
        Complete login flow
        Returns (response, error_message)
        """
        user, error = await self.authenticate(request)
        
        if error:
            return None, error
        
        # Check if 2FA is required
        if user.is_2fa_enabled:
            return LoginResponse(
                access_token="",
                refresh_token="",
                token_type="bearer",
                expires_in=0,
                user_id=str(user.id),
                requires_2fa=True
            ), None
        
        # Generate tokens
        access_token = self.create_access_token(str(user.id), user.role.value)
        refresh_token = self.create_refresh_token(str(user.id))
        
        logger.info("User logged in", user_id=str(user.id))
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=str(user.id),
            requires_2fa=False
        ), None
    
    async def register(self, request: RegisterRequest) -> Tuple[Optional[RegisterResponse], Optional[str]]:
        """Register a new user"""
        # Check if email already exists
        existing = await self.get_user_by_email(request.email)
        if existing:
            return None, "Email already registered"
        
        # Check if phone already exists
        result = await self.session.execute(
            select(User).where(User.phone == request.phone)
        )
        if result.scalar_one_or_none():
            return None, "Phone number already registered"
        
        # Create user
        from app.models.user import UserProfile
        
        user = User(
            email=request.email.lower(),
            phone=request.phone,
            password_hash=self.hash_password(request.password),
            role=UserRole.CUSTOMER,
            status=UserStatus.PENDING,
        )
        
        profile = UserProfile(
            user=user,
            first_name=request.first_name,
            last_name=request.last_name,
        )
        
        self.session.add(user)
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(user)
        
        logger.info("New user registered", user_id=str(user.id), email=user.email)
        
        # TODO: Send verification email
        
        return RegisterResponse(
            user_id=str(user.id),
            email=user.email,
            message="Registration successful. Please verify your email."
        ), None
    
    async def refresh_access_token(self, request: RefreshTokenRequest) -> Tuple[Optional[str], Optional[str]]:
        """Refresh access token using refresh token"""
        payload = self.decode_token(request.refresh_token)
        
        if not payload:
            return None, "Invalid refresh token"
        
        if payload.type != "refresh":
            return None, "Invalid token type"
        
        user = await self.get_user_by_id(UUID(payload.sub))
        
        if not user or user.status in [UserStatus.BLOCKED, UserStatus.CLOSED]:
            return None, "User not found or inactive"
        
        access_token = self.create_access_token(str(user.id), user.role.value)
        
        return access_token, None
    
    async def verify_2fa(self, user_id: str, totp_code: str) -> Tuple[Optional[LoginResponse], Optional[str]]:
        """Verify 2FA and complete login"""
        user = await self.get_user_by_id(UUID(user_id))
        
        if not user:
            return None, "User not found"
        
        if not user.totp_secret:
            return None, "2FA not enabled"
        
        if not self.verify_totp(user.totp_secret, totp_code):
            return None, "Invalid 2FA code"
        
        # Generate tokens
        access_token = self.create_access_token(str(user.id), user.role.value)
        refresh_token = self.create_refresh_token(str(user.id))
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=str(user.id),
            requires_2fa=False
        ), None
    
    async def enable_2fa(self, user_id: UUID) -> Tuple[Optional[dict], Optional[str]]:
        """Enable 2FA for user"""
        user = await self.get_user_by_id(user_id)
        
        if not user:
            return None, "User not found"
        
        if user.is_2fa_enabled:
            return None, "2FA already enabled"
        
        secret = self.generate_totp_secret()
        uri = self.get_totp_uri(secret, user.email)
        
        # Store secret temporarily (should be confirmed before final save)
        user.totp_secret = secret
        await self.session.commit()
        
        return {
            "secret": secret,
            "uri": uri,
            "message": "Scan QR code with authenticator app and verify"
        }, None
    
    async def confirm_2fa(self, user_id: UUID, totp_code: str) -> Tuple[bool, Optional[str]]:
        """Confirm 2FA setup"""
        user = await self.get_user_by_id(user_id)
        
        if not user or not user.totp_secret:
            return False, "2FA not initialized"
        
        if not self.verify_totp(user.totp_secret, totp_code):
            return False, "Invalid verification code"
        
        user.is_2fa_enabled = True
        await self.session.commit()
        
        logger.info("2FA enabled", user_id=str(user.id))
        
        return True, None
    
    async def disable_2fa(self, user_id: UUID, totp_code: str) -> Tuple[bool, Optional[str]]:
        """Disable 2FA for user"""
        user = await self.get_user_by_id(user_id)
        
        if not user:
            return False, "User not found"
        
        if not user.is_2fa_enabled:
            return False, "2FA not enabled"
        
        if not self.verify_totp(user.totp_secret, totp_code):
            return False, "Invalid verification code"
        
        user.is_2fa_enabled = False
        user.totp_secret = None
        await self.session.commit()
        
        logger.info("2FA disabled", user_id=str(user.id))
        
        return True, None
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate email/phone verification token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_reset_token() -> str:
        """Generate password reset token"""
        return secrets.token_urlsafe(32)

