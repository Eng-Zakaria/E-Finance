"""
E-Finance Core Banking Configuration
Environment-based configuration management
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "E-Finance Core Banking API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")
    SECRET_KEY: str = Field(default="super-secret-key-change-in-production")
    WORKERS: int = Field(default=4)
    
    # API
    API_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://localhost:8080"])
    
    # JWT Authentication
    JWT_SECRET_KEY: str = Field(default="jwt-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database - PostgreSQL
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_USER: str = Field(default="efinance")
    POSTGRES_PASSWORD: str = Field(default="efinance123")
    POSTGRES_DB: str = Field(default="efinance_core")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def SYNC_DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # MongoDB
    MONGODB_URI: str = Field(default="mongodb://localhost:27017")
    MONGODB_DB: str = Field(default="efinance_documents")
    
    # Redis
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_DB: int = Field(default=0)
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Elasticsearch
    ELASTICSEARCH_HOST: str = Field(default="http://localhost:9200")
    ELASTICSEARCH_USER: Optional[str] = Field(default=None)
    ELASTICSEARCH_PASSWORD: Optional[str] = Field(default=None)
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092")
    KAFKA_CONSUMER_GROUP: str = Field(default="efinance-core")
    
    # External Services
    FRAUD_DETECTION_URL: str = Field(default="http://localhost:8001")
    WEB3_SERVICE_URL: str = Field(default="http://localhost:8002")
    BNPL_SERVICE_URL: str = Field(default="http://localhost:8003")
    NOTIFICATION_SERVICE_URL: str = Field(default="http://localhost:8004")
    
    # Payment Gateways
    STRIPE_SECRET_KEY: Optional[str] = Field(default=None)
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(default=None)
    
    # Plaid (Bank integrations)
    PLAID_CLIENT_ID: Optional[str] = Field(default=None)
    PLAID_SECRET: Optional[str] = Field(default=None)
    PLAID_ENVIRONMENT: str = Field(default="sandbox")
    
    # Twilio (SMS)
    TWILIO_ACCOUNT_SID: Optional[str] = Field(default=None)
    TWILIO_AUTH_TOKEN: Optional[str] = Field(default=None)
    TWILIO_PHONE_NUMBER: Optional[str] = Field(default=None)
    
    # SendGrid (Email)
    SENDGRID_API_KEY: Optional[str] = Field(default=None)
    SENDGRID_FROM_EMAIL: str = Field(default="noreply@efinance.com")
    
    # AWS
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None)
    AWS_REGION: str = Field(default="us-east-1")
    AWS_S3_BUCKET: Optional[str] = Field(default=None)
    
    # Azure
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = Field(default=None)
    AZURE_CONTAINER_NAME: Optional[str] = Field(default=None)
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=1000)
    RATE_LIMIT_WINDOW: int = Field(default=60)  # seconds
    
    # Security
    BCRYPT_ROUNDS: int = Field(default=12)
    PASSWORD_MIN_LENGTH: int = Field(default=8)
    MAX_LOGIN_ATTEMPTS: int = Field(default=5)
    LOCKOUT_DURATION_MINUTES: int = Field(default=30)
    
    # Transaction Limits (in cents)
    DEFAULT_DAILY_TRANSFER_LIMIT: int = Field(default=1000000)  # $10,000
    DEFAULT_MONTHLY_TRANSFER_LIMIT: int = Field(default=10000000)  # $100,000
    DEFAULT_DAILY_WITHDRAWAL_LIMIT: int = Field(default=500000)  # $5,000
    
    # Feature Flags
    ENABLE_CRYPTO: bool = Field(default=True)
    ENABLE_BNPL: bool = Field(default=True)
    ENABLE_INTERNATIONAL_TRANSFERS: bool = Field(default=True)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
