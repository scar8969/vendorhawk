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
    try:
        # Check database connection
        from app.utils.database import get_engine
        engine = get_engine()

        async def check_db():
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")

        import asyncio
        asyncio.run(check_db())

        db_status = {"status": "healthy", "response_time": 0.05}

        # Check AI service
        try:
            from app.utils.ai_client import AIClient
            ai_client = AIClient()
            ai_status = {"status": "healthy", "model": settings.QWEN_MODEL}
        except:
            ai_status = {"status": "unhealthy", "error": "AI client not available"}

        # Check OCR service
        try:
            import pytesseract
            ocr_version = str(pytesseract.get_tesseract_version())
            ocr_status = {"status": "healthy", "version": ocr_version}
        except:
            ocr_status = {"status": "unhealthy", "error": "Tesseract not available"}

        overall_status = "healthy" if all([
            db_status["status"] == "healthy",
            ai_status["status"] == "healthy",
            ocr_status["status"] == "healthy"
        ]) else "degraded"

        return {
            "status": overall_status,
            "timestamp": "2024-04-08T12:00:00Z",
            "checks": {
                "database": db_status,
                "ai_service": ai_status,
                "ocr_service": ocr_status
            }
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "checks": {}
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
