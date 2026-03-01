"""
Fraud Detection Service Configuration
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    APP_NAME: str = "E-Finance Fraud Detection"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    
    # Database
    DATABASE_URL: str = Field(default="postgresql+asyncpg://efinance:efinance123@localhost:5432/efinance_fraud")
    
    # Redis for caching
    REDIS_URL: str = Field(default="redis://localhost:6379/1")
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092")
    KAFKA_TRANSACTION_TOPIC: str = Field(default="transactions")
    KAFKA_ALERTS_TOPIC: str = Field(default="fraud-alerts")
    
    # ML Models
    MODEL_PATH: str = Field(default="./models")
    FRAUD_MODEL_NAME: str = Field(default="fraud_detection_model.joblib")
    ANOMALY_MODEL_NAME: str = Field(default="anomaly_detection_model.joblib")
    
    # Thresholds
    FRAUD_SCORE_THRESHOLD: float = Field(default=0.7)
    HIGH_RISK_THRESHOLD: float = Field(default=0.85)
    CRITICAL_RISK_THRESHOLD: float = Field(default=0.95)
    
    # AML Settings
    LARGE_TRANSACTION_THRESHOLD: int = Field(default=1000000)  # $10,000 in cents
    STRUCTURING_THRESHOLD: int = Field(default=950000)  # Just under $10K
    VELOCITY_CHECK_WINDOW_HOURS: int = Field(default=24)
    MAX_DAILY_TRANSACTIONS: int = Field(default=50)
    MAX_DAILY_AMOUNT: int = Field(default=5000000)  # $50,000
    
    # Core Banking API
    CORE_BANKING_URL: str = Field(default="http://localhost:8000")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

