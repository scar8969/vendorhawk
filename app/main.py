"""
ProcureAI Main Application

FastAPI application for AI-powered procurement agent.
Handles invoice processing, price checking, and vendor negotiation.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.api import invoices, negotiations, factories, vendors, admin
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting ProcureAI API...", version=settings.APP_VERSION)
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'local'}")

    # Initialize database connection pool
    from app.utils.database import init_db
    await init_db()

    # Initialize external service clients
    from app.utils.ai_client import AIClient
    from app.utils.ocr_client import OCRClient

    app.state.ai_client = AIClient()
    app.state.ocr_client = OCRClient()

    logger.info("ProcureAI API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down ProcureAI API...")
    # Close database connections
    # Cleanup external service connections
    logger.info("ProcureAI API stopped")


# Create FastAPI application
app = FastAPI(
    title="ProcureAI",
    description="AI-powered procurement agent for Indian MSME manufacturers",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    lifespan=lifespan
)

# Rate limit exception handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(invoices.router, prefix="/api", tags=["invoices"])
app.include_router(negotiations.router, prefix="/api", tags=["negotiations"])
app.include_router(factories.router, prefix="/api", tags=["factories"])
app.include_router(vendors.router, prefix="/api", tags=["vendors"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/")
@limiter.limit("100/minute")
async def root():
    """
    Root endpoint
    Provides basic API information
    """
    return {
        "name": "ProcureAI API",
        "version": settings.APP_VERSION,
        "status": "operational",
        "description": "AI-powered procurement agent for Indian MSME manufacturers",
        "documentation": "/docs" if settings.APP_ENV != "production" else None,
        "health_check": "/health"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    Returns system health status
    """
    from app.utils.database import check_db_health
    from app.utils.ai_client import check_ai_health

    db_health = await check_db_health()
    ai_health = await check_ai_health()

    overall_status = "healthy" if all([
        db_health["status"] == "healthy",
        ai_health["status"] == "healthy"
    ]) else "degraded"

    return {
        "status": overall_status,
        "timestamp": logger.info("Health check performed"),
        "checks": {
            "database": db_health,
            "ai_service": ai_health
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.APP_ENV == "development",
        log_level="info"
    )
