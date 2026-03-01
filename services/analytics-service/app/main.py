"""
Analytics Service
FastAPI application with Spark integration
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.config import settings

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
    logger.info("Starting Analytics Service", version=settings.APP_VERSION)
    
    # Initialize Spark session
    from app.spark.session import get_spark_session
    spark = get_spark_session()
    logger.info("Spark session initialized", app_name=spark.sparkContext.appName)
    
    yield
    
    # Stop Spark
    spark.stop()
    logger.info("Shutting down Analytics Service")


def create_application() -> FastAPI:
    """Create FastAPI application"""
    
    application = FastAPI(
        title="E-Finance Analytics Service",
        description="""
        ## 📊 Financial Analytics Service
        
        Apache Spark-powered analytics:
        - **Transaction Analytics** - Volume, trends, patterns
        - **Risk Analytics** - Risk scoring, anomaly detection
        - **Customer Analytics** - Segmentation, behavior
        - **Financial Reports** - Statements, summaries
        - **Real-time Dashboards** - Live metrics
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
    
    # Include API routes
    from app.api import router
    application.include_router(router, prefix="/api/v1")
    
    @application.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "service": "analytics-service"
        }
    
    return application


app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8004, reload=True)

