"""
Negotiation Management API

Handles vendor negotiation operations including starting negotiations,
tracking progress, and confirming orders.
"""

from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.utils.database import get_db
from app.utils.logger import get_logger

router = APIRouter(prefix="/negotiations", tags=["negotiations"])
limiter = Limiter(key_func=get_remote_address)
logger = get_logger(__name__)


@router.post("/start/{invoice_id}")
@limiter.limit("5/minute")
async def start_negotiation(
    invoice_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Start vendor negotiation for an invoice

    Flow:
    1. Validate invoice exists and price check completed
    2. Detect overpayment (> 5%)
    3. Select top 50 vendors by commodity/region
    4. Generate personalized messages with Qwen
    5. Send messages via email/notification
    6. Start background task to monitor responses
    7. Return negotiation tracking ID

    Args:
        invoice_id: Invoice UUID
        background_tasks: FastAPI background tasks

    Returns:
        NegotiationResponse with tracking details

    Raises:
        HTTPException: If negotiation cannot be started
    """
    try:
        logger.info("Start negotiation requested", invoice_id=invoice_id)

        # Import negotiation engine
        from app.services.negotiation_engine import NegotiationEngine

        # Get factory_id from auth context (for now, use placeholder)
        # In production, this would come from JWT token
        factory_id = "test-factory-id"  # TODO: Get from auth context

        # Start negotiation
        engine = NegotiationEngine(db)
        negotiation = await engine.start_negotiation(
            invoice_id=invoice_id,
            factory_id=factory_id,
        )

        return {
            "negotiation_id": str(negotiation.id),
            "invoice_id": invoice_id,
            "factory_id": factory_id,
            "commodity": negotiation.commodity,
            "quantity": float(negotiation.quantity),
            "unit": negotiation.unit,
            "target_price": float(negotiation.target_price),
            "status": negotiation.status,
            "vendors_contacted": 50,  # Will be actual count after implementation
            "estimated_completion": "2024-04-08T14:30:00Z",  # 2 hours from now
            "started_at": negotiation.started_at.isoformat(),
        }

    except ValueError as e:
        logger.error("Negotiation validation failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Start negotiation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start negotiation: {str(e)}")


@router.get("/{negotiation_id}")
async def get_negotiation_status(
    negotiation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get real-time negotiation status

    Returns current negotiation progress including:
    - Vendors contacted
    - Responses received
    - Best quote so far
    - Time remaining

    Args:
        negotiation_id: Negotiation UUID

    Returns:
        NegotiationStatus with current progress

    Raises:
        HTTPException: If negotiation not found
    """
    try:
        logger.info("Get negotiation status requested", negotiation_id=negotiation_id)

        # Import negotiation engine
        from app.services.negotiation_engine import NegotiationEngine

        # Get negotiation status
        engine = NegotiationEngine(db)
        status = await engine.get_negotiation_status(negotiation_id)

        return status

    except ValueError as e:
        logger.error("Negotiation not found", error=str(e))
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Get negotiation status failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/{negotiation_id}/confirm")
async def confirm_order(
    negotiation_id: str,
    vendor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm order with best quote vendor

    Finalizes the negotiation by:
    1. Validating negotiation is complete
    2. Getting best confirmed quote
    3. Calculating savings
    4. Sending confirmation to vendor
    5. Updating negotiation status
    6. Storing savings record

    Args:
        negotiation_id: Negotiation UUID
        vendor_id: Winning vendor UUID

    Returns:
        Confirmation details with savings amount

    Raises:
        HTTPException: If confirmation fails
    """
    try:
        logger.info("Confirm order requested", negotiation_id=negotiation_id, vendor_id=vendor_id)

        # Import negotiation engine
        from app.services.negotiation_engine import NegotiationEngine

        # Confirm order
        engine = NegotiationEngine(db)
        confirmation = await engine.confirm_order(
            negotiation_id=negotiation_id,
            vendor_id=vendor_id,
        )

        return confirmation

    except ValueError as e:
        logger.error("Order confirmation validation failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Confirm order failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to confirm order: {str(e)}")
