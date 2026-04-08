"""
Database Connection and Session Management

Provides async database connection pooling and session management
using SQLAlchemy with asyncpg driver.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Base class for all models
Base = declarative_base()

# Database engine (created on first use)
_engine = None
_async_session_maker = None


def get_engine():
    """
    Get or create database engine

    Returns:
        AsyncEngine: SQLAlchemy async engine
    """
    global _engine

    if _engine is None:
        # Convert postgresql:// to postgresql+asyncpg:// if needed
        database_url = settings.DATABASE_URL
        if not database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        logger.info("Creating database engine", database=database_url.split("@")[1])

        _engine = create_async_engine(
            database_url,
            echo=settings.ENABLE_DEBUG_LOGGING,
            pool_size=20,  # Max connections in pool
            max_overflow=10,  # Additional connections under load
            pool_timeout=30,  # Wait time for connection
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_pre_ping=True,  # Test connections before use
        )

    return _engine


def get_session_maker():
    """
    Get or create session maker

    Returns:
        async_sessionmaker: SQLAlchemy async session maker
    """
    global _async_session_maker

    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    return _async_session_maker


async def init_db() -> None:
    """
    Initialize database connection pool

    Called during application startup to ensure connection pool
    is ready and perform any necessary migrations.
    """
    try:
        engine = get_engine()

        # Test connection
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")

        logger.info("Database connection pool initialized successfully")

    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


async def close_db() -> None:
    """
    Close database connection pool

    Called during application shutdown to cleanly close connections.
    """
    global _engine

    if _engine is not None:
        await _engine.dispose()
        logger.info("Database connection pool closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for dependency injection

    Yields:
        AsyncSession: Database session

    Example:
        @app.get("/api/invoices")
        async def get_invoices(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Invoice))
            return result.scalars().all()
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions

    Yields:
        AsyncSession: Database session

    Example:
        async with get_db_context() as db:
            result = await db.execute(select(Invoice))
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> dict:
    """
    Check database health status

    Returns:
        dict: Health check result with status and response time
    """
    import time

    start_time = time.time()

    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")

        response_time = time.time() - start_time

        return {
            "status": "healthy",
            "response_time": round(response_time, 3),
            "connection_pool": f"{engine.pool.size()}/{engine.pool.size()} used"
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
