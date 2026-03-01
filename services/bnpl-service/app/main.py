"""
BNPL Service
Main FastAPI application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import structlog

from app.config import settings
from app.api import router

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
    logger.info("Starting BNPL Service", version=settings.APP_VERSION)
    yield
    logger.info("Shutting down BNPL Service")


def create_application() -> FastAPI:
    """Create FastAPI application"""
    
    application = FastAPI(
        title="E-Finance BNPL Service",
        description="""
        ## 💳 Buy Now Pay Later Service
        
        Installment payment platform (similar to Tabby/Valu):
        - **Credit Assessment** - Instant credit scoring
        - **Installment Plans** - Split payments into installments
        - **Merchant Integration** - Partner merchant support
        - **Payment Scheduling** - Automated payment collection
        - **Credit Limits** - Dynamic credit limit management
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
            "service": "bnpl-service"
        }
    
    return application


app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8003, reload=True)

