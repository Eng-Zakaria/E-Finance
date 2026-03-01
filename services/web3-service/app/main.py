"""
Web3/Blockchain Service
Main FastAPI application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import structlog

from app.config import settings
from app.api import router
from app.blockchain.ethereum import ethereum_client
from app.blockchain.wallet_manager import wallet_manager

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Web3 Service", version=settings.APP_VERSION)
    
    # Initialize blockchain connections
    await ethereum_client.connect()
    logger.info("Ethereum client connected")
    
    yield
    
    # Cleanup
    await ethereum_client.disconnect()
    logger.info("Shutting down Web3 Service")


def create_application() -> FastAPI:
    """Create FastAPI application"""
    
    application = FastAPI(
        title="E-Finance Web3 Service",
        description="""
        ## 🔗 Web3 & Blockchain Service
        
        Cryptocurrency and blockchain integration:
        - **Wallet Management** - Create and manage crypto wallets
        - **Token Operations** - ERC-20 token support
        - **Transactions** - Send/receive crypto
        - **DeFi Integration** - Lending, staking, swaps
        - **NFT Support** - ERC-721/1155 tokens
        - **Multi-chain** - Ethereum, BSC, Polygon
        """,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )
    
    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Prometheus metrics
    metrics_app = make_asgi_app()
    application.mount("/metrics", metrics_app)
    
    # Include API routes
    application.include_router(router, prefix="/api/v1")
    
    @application.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "service": "web3-service",
            "ethereum_connected": ethereum_client.is_connected
        }
    
    return application


app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)

