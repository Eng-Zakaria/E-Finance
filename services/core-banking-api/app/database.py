"""
Database configuration and connection management
Supports PostgreSQL (primary), MongoDB (documents), Redis (cache)
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


class Base(DeclarativeBase):
    """SQLAlchemy declarative base"""
    metadata = MetaData(naming_convention=convention)


# PostgreSQL Async Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Database:
    """Database connection manager"""
    
    def __init__(self):
        self._mongo_client: AsyncIOMotorClient | None = None
        self._redis_client: Redis | None = None
    
    async def connect(self):
        """Connect to all databases"""
        # MongoDB
        self._mongo_client = AsyncIOMotorClient(settings.MONGODB_URI)
        logger.info("MongoDB connected", uri=settings.MONGODB_URI)
        
        # Redis
        self._redis_client = Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await self._redis_client.ping()
        logger.info("Redis connected", url=settings.REDIS_URL)
    
    async def disconnect(self):
        """Disconnect from all databases"""
        if self._mongo_client:
            self._mongo_client.close()
            logger.info("MongoDB disconnected")
        
        if self._redis_client:
            await self._redis_client.close()
            logger.info("Redis disconnected")
    
    @property
    def mongo(self) -> AsyncIOMotorClient:
        """Get MongoDB client"""
        if not self._mongo_client:
            raise RuntimeError("MongoDB not connected")
        return self._mongo_client[settings.MONGODB_DB]
    
    @property
    def redis(self) -> Redis:
        """Get Redis client"""
        if not self._redis_client:
            raise RuntimeError("Redis not connected")
        return self._redis_client


# Global database instance
database = Database()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        # Import all models to ensure they're registered
        from app.models import user, account, transaction, card
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for getting async database session"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_mongo():
    """Dependency for getting MongoDB database"""
    return database.mongo


def get_redis():
    """Dependency for getting Redis client"""
    return database.redis
