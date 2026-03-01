"""
Web3 Service Configuration
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    APP_NAME: str = "E-Finance Web3 Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    
    # Database
    DATABASE_URL: str = Field(default="postgresql+asyncpg://efinance:efinance123@localhost:5432/efinance_web3")
    
    # Redis for caching
    REDIS_URL: str = Field(default="redis://localhost:6379/2")
    
    # Ethereum
    ETHEREUM_RPC_URL: str = Field(default="https://mainnet.infura.io/v3/YOUR_PROJECT_ID")
    ETHEREUM_WS_URL: str = Field(default="wss://mainnet.infura.io/ws/v3/YOUR_PROJECT_ID")
    ETHEREUM_CHAIN_ID: int = Field(default=1)  # 1 = mainnet, 5 = goerli, 11155111 = sepolia
    
    # Other chains
    BSC_RPC_URL: str = Field(default="https://bsc-dataseed.binance.org/")
    POLYGON_RPC_URL: str = Field(default="https://polygon-rpc.com/")
    
    # Wallet encryption
    WALLET_ENCRYPTION_KEY: str = Field(default="your-encryption-key-here")
    
    # Gas settings
    DEFAULT_GAS_LIMIT: int = Field(default=21000)
    MAX_GAS_PRICE_GWEI: int = Field(default=100)
    
    # Token addresses (mainnet)
    USDT_CONTRACT: str = Field(default="0xdAC17F958D2ee523a2206206994597C13D831ec7")
    USDC_CONTRACT: str = Field(default="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    WETH_CONTRACT: str = Field(default="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
    
    # DeFi protocols
    UNISWAP_ROUTER: str = Field(default="0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
    AAVE_LENDING_POOL: str = Field(default="0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9")
    
    # Core Banking API
    CORE_BANKING_URL: str = Field(default="http://localhost:8000")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

