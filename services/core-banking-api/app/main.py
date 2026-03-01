"""
E-Finance Core Banking API
Main FastAPI application entry point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_client import make_asgi_app
import structlog

from app.config import settings
from app.api.v1 import router as api_v1_router
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.database import database, init_db
from app.events import create_start_app_handler, create_stop_app_handler

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
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
    # Startup
    logger.info("Starting E-Finance Core Banking API", version=settings.APP_VERSION)
    await init_db()
    await database.connect()
    logger.info("Database connected successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down E-Finance Core Banking API")
    await database.disconnect()
    logger.info("Database disconnected")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    application = FastAPI(
        title="E-Finance Core Banking API",
        description="""
        ## 🏦 E-Finance Core Banking Platform
        
        A comprehensive digital banking API with:
        - **Account Management** - Create, manage, and monitor bank accounts
        - **Fund Transfers** - Internal, domestic, and international transfers
        - **Bill Payments** - Pay bills and schedule recurring payments
        - **Cards Management** - Virtual and physical card operations
        - **KYC/AML** - Identity verification and compliance checks
        - **Notifications** - Real-time alerts and notifications
        
        ### Authentication
        All endpoints require JWT Bearer token authentication.
        
        ### Rate Limiting
        - Standard: 1000 requests/minute
        - Premium: 5000 requests/minute
        """,
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # CORS Middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # GZip Middleware
    application.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Custom Middlewares
    application.add_middleware(LoggingMiddleware)
    application.add_middleware(RateLimitMiddleware)
    
    # Mount Prometheus metrics
    metrics_app = make_asgi_app()
    application.mount("/metrics", metrics_app)
    
    # Include API routers
    application.include_router(api_v1_router, prefix="/api/v1")
    
    @application.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "service": "core-banking-api"
        }
    
    @application.get("/", tags=["Root"])
    async def root():
        """Root endpoint"""
        return {
            "message": "Welcome to E-Finance Core Banking API",
            "docs": "/docs",
            "version": settings.APP_VERSION
        }
    
    return application


app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=settings.WORKERS
    )

