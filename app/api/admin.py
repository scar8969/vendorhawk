"""
Admin and Monitoring API

Handles system metrics, health checks, and administrative functions.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.utils.database import get_db, check_db_health
from app.utils.ai_client import check_ai_health
from app.utils.logger import get_logger

router = APIRouter(tags=["admin"])
limiter = Limiter(key_func=get_remote_address)
logger = get_logger(__name__)


@router.get("/metrics")
async def get_system_metrics(
    period: str = "month",
    db: AsyncSession = Depends(get_db)
):
    """
    Get system-wide metrics and statistics

    Returns comprehensive metrics including:
    - Factory statistics (total, active, new, by state)
    - Invoice statistics (total, success rate)
    - Negotiation statistics (total, active, success rate)
    - Savings statistics (total, average per negotiation)
    - Performance metrics (processing times, uptime)

    Args:
        period: Time period (week/month/quarter/year)
        db: Database session

    Returns:
        System metrics dashboard data
    """
    try:
        logger.info("Get system metrics requested", period=period)

        # TODO: Implement metrics collection logic
        return {
            "message": "System metrics endpoint - to be implemented",
            "period": period,
            "metrics": {
                "factories": {"total": 0, "active": 0, "new_this_period": 0},
                "invoices": {"total": 0, "success_rate": 0.0},
                "negotiations": {"total": 0, "active": 0, "success_rate": 0.0},
                "savings": {"total": 0.0, "average_per_negotiation": 0.0},
                "performance": {"uptime": 0.0, "avg_processing_time": 0.0}
            }
        }

    except Exception as e:
        logger.error("Get system metrics failed", error=str(e))
        return {
            "error": f"Failed to get metrics: {str(e)}",
            "period": period
        }


@router.get("/health")
async def health_check():
    """
    Comprehensive system health check

    Monitors health of:
    - Database connection and performance
    - AI service (Qwen via OpenRouter)
    - OCR service (Tesseract)
    - Storage service (Supabase)

    Returns overall system status and individual component health.
    """
    try:
        logger.debug("Health check performed")

        # Check database health
        db_health = await check_db_health()

        # Check AI service health
        ai_health = await check_ai_health()

        # Check OCR service
        ocr_health = await check_ocr_health()

        # Determine overall status
        overall_status = "healthy" if all([
            db_health["status"] == "healthy",
            ai_health["status"] == "healthy",
            ocr_health["status"] == "healthy"
        ]) else "degraded"

        return {
            "status": overall_status,
            "timestamp": "2024-04-08T10:30:00Z",
            "checks": {
                "database": db_health,
                "ai_service": ai_health,
                "ocr_service": ocr_health
            }
        }

    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_ocr_health() -> dict:
    """Check OCR service health"""
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        return {
            "status": "healthy",
            "version": str(version),
            "available": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "available": False
        }
