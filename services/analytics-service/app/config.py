"""
Analytics Service Configuration
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    APP_NAME: str = "E-Finance Analytics"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    
    # Spark
    SPARK_MASTER: str = Field(default="local[*]")
    SPARK_APP_NAME: str = Field(default="efinance-analytics")
    SPARK_DRIVER_MEMORY: str = Field(default="2g")
    SPARK_EXECUTOR_MEMORY: str = Field(default="2g")
    
    # Database
    POSTGRES_URL: str = Field(default="jdbc:postgresql://localhost:5432/efinance_core")
    POSTGRES_USER: str = Field(default="efinance")
    POSTGRES_PASSWORD: str = Field(default="efinance123")
    
    # Data Lake
    DATA_LAKE_PATH: str = Field(default="/tmp/efinance-datalake")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

