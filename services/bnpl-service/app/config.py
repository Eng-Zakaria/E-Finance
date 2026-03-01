"""
BNPL Service Configuration
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    APP_NAME: str = "E-Finance BNPL Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    
    # Database
    DATABASE_URL: str = Field(default="postgresql+asyncpg://efinance:efinance123@localhost:5432/efinance_bnpl")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/3")
    
    # MongoDB for documents
    MONGODB_URI: str = Field(default="mongodb://localhost:27017")
    MONGODB_DB: str = Field(default="efinance_bnpl")
    
    # Credit Scoring
    MIN_CREDIT_SCORE: int = Field(default=300)
    MAX_CREDIT_SCORE: int = Field(default=850)
    MIN_APPROVAL_SCORE: int = Field(default=550)
    
    # Limits
    MIN_PURCHASE_AMOUNT: int = Field(default=5000)  # $50 in cents
    MAX_PURCHASE_AMOUNT: int = Field(default=500000)  # $5000 in cents
    DEFAULT_CREDIT_LIMIT: int = Field(default=100000)  # $1000 in cents
    MAX_CREDIT_LIMIT: int = Field(default=1000000)  # $10000 in cents
    
    # Interest/Fees
    BASE_INTEREST_RATE: float = Field(default=0.0)  # 0% for promotional
    LATE_FEE_PERCENT: float = Field(default=0.05)  # 5% late fee
    LATE_FEE_FIXED: int = Field(default=1500)  # $15 fixed late fee
    GRACE_PERIOD_DAYS: int = Field(default=3)
    
    # Installment options
    INSTALLMENT_OPTIONS: list = Field(default=[3, 4, 6, 12])  # Number of installments
    
    # Core Banking API
    CORE_BANKING_URL: str = Field(default="http://localhost:8000")
    FRAUD_DETECTION_URL: str = Field(default="http://localhost:8001")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

