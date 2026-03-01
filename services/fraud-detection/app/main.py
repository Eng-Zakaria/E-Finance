"""
Fraud Detection Service
Main FastAPI application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import structlog

from app.config import settings
from app.api import router
from app.ml.model_manager import model_manager

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
    logger.info("Starting Fraud Detection Service", version=settings.APP_VERSION)
    
    # Load ML models
    await model_manager.load_models()
    logger.info("ML models loaded successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Fraud Detection Service")


def create_application() -> FastAPI:
    """Create FastAPI application"""
    
    application = FastAPI(
        title="E-Finance Fraud Detection Service",
        description="""
        ## 🛡️ Fraud Detection & AML Service
        
        Machine learning powered fraud detection system with:
        - **Real-time Transaction Scoring** - Instant risk assessment
        - **Anomaly Detection** - Identify unusual patterns
        - **AML Screening** - Anti-money laundering checks
        - **Rule-based Alerts** - Configurable fraud rules
        - **Behavioral Analysis** - User behavior profiling
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
            "service": "fraud-detection",
            "models_loaded": model_manager.models_loaded
        }
    
    return application


app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)

