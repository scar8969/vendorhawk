"""
Negotiation Engine Service

Orchestrates autonomous vendor negotiation with:
1. Vendor selection and outreach
2. Personalized message generation (Hinglish)
3. Response monitoring and parsing
4. Counter-offer logic
5. Best quote selection
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from decimal import Decimal

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Negotiation, NegotiationVendorMessage, Vendor, Invoice
from app.services.vendor_selector import VendorSelector
from app.utils.ai_client import AIClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NegotiationEngine:
    """
    Negotiation engine service

    Manages end-to-end vendor negotiation process from initiation
    to best quote selection.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize negotiation engine

        Args:
            db: Database session
        """
        self.db = db
        self.ai_client = AIClient()
        self.vendor_selector = VendorSelector(db)

    async def start_negotiation(
        self,
        invoice_id: str,
        factory_id: str,
    ) -> Negotiation:
        """
        Start vendor negotiation for an invoice

        Process:
        1. Validate invoice and price check
        2. Select vendors for negotiation
        3. Generate personalized messages
        4. Send initial messages
        5. Start response monitoring

        Args:
            invoice_id: Invoice UUID
            factory_id: Factory UUID

        Returns:
            Created negotiation record

        Raises:
            ValueError: If negotiation cannot be started
        """
        try:
            logger.info(
                "Starting negotiation",
                invoice_id=invoice_id,
                factory_id=factory_id,
            )

            # Step 1: Get invoice details
            invoice = await self._get_invoice(invoice_id)
            if not invoice:
                raise ValueError(f"Invoice not found: {invoice_id}")

            # Step 2: Detect commodity
            from app.services.invoice_processor import CommodityMapper
            commodity = CommodityMapper.map_to_commodity(invoice.item_name)
            if not commodity:
                raise ValueError(
                    f"Could not identify commodity for: {invoice.item_name}"
                )

            # Step 3: Select vendors
            vendors = await self.vendor_selector.select_vendors_for_negotiation(
                commodity=commodity,
                city=invoice.factory.city if invoice.factory else "Mumbai",
                state=invoice.factory.state if invoice.factory else "Maharashtra",
                quantity=float(invoice.quantity),
                limit=50,
            )

            if not vendors:
                raise ValueError(
                    f"No suitable vendors found for commodity: {commodity}"
                )

            # Step 4: Create negotiation record
            negotiation = Negotiation(
                invoice_id=invoice_id,
                factory_id=factory_id,
                commodity=commodity,
                quantity=float(invoice.quantity),
                unit=invoice.unit,
                target_price=float(invoice.unit_price) * 0.95,  # Target 5% savings
                status="active",
                started_at=datetime.now(),
            )

            self.db.add(negotiation)
            await self.db.commit()
            await self.db.refresh(negotiation)

            logger.info(
                "Negotiation created",
                negotiation_id=negotiation.id,
                vendors_selected=len(vendors),
            )

            # Step 5: Generate and send messages
            await self._send_initial_messages(
                negotiation, vendors, invoice
            )

            # Step 6: Start response monitoring (background task)
            asyncio.create_task(
                self._monitor_vendor_responses(negotiation.id)
            )

            return negotiation

        except Exception as e:
            logger.error("Failed to start negotiation", error=str(e))
            raise

    async def _get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """
        Get invoice with factory details

        Args:
            invoice_id: Invoice UUID

        Returns:
            Invoice object with factory relation
        """
        query = (
            select(Invoice)
            .options(selectinload(Invoice.factory))
            .where(Invoice.id == invoice_id)
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _send_initial_messages(
        self,
        negotiation: Negotiation,
        vendors: List[Vendor],
        invoice: Invoice,
    ) -> None:
        """
        Send initial negotiation messages to all selected vendors

        Args:
            negotiation: Negotiation record
            vendors: List of selected vendors
            invoice: Original invoice
        """
        logger.info(
            "Sending initial messages",
            negotiation_id=negotiation.id,
            vendor_count=len(vendors),
        )

        for vendor in vendors:
            try:
                # Generate personalized message
                message = await self.ai_client.generate_negotiation_message(
                    vendor_name=vendor.name,
                    commodity=negotiation.commodity,
                    quantity=float(negotiation.quantity),
                    unit=negotiation.unit,
                    target_price=float(negotiation.target_price),
                    factory_name=invoice.factory.name if invoice.factory else None,
                )

                # Create message record
                vendor_message = NegotiationVendorMessage(
                    negotiation_id=negotiation.id,
                    vendor_id=vendor.id,
                    message_sent=message,
                    message_sent_at=datetime.now(),
                    final_status="pending",
                )

                self.db.add(vendor_message)

                # TODO: Send actual message via email/SMS/WhatsApp
                # For now, just log it
                logger.debug(
                    "Message sent to vendor",
                    negotiation_id=negotiation.id,
                    vendor_id=vendor.id,
                    vendor_name=vendor.name,
                    message_length=len(message),
                )

            except Exception as e:
                logger.error(
                    "Failed to send message to vendor",
                    vendor_id=vendor.id,
                    error=str(e),
                )

        # Commit all message records
        await self.db.commit()

        logger.info(
            "Initial messages sent",
            negotiation_id=negotiation.id,
            total_messages=len(vendors),
        )

    async def _monitor_vendor_responses(
        self,
        negotiation_id: str,
        timeout_hours: int = 2,
    ) -> None:
        """
        Monitor vendor responses during negotiation window

        Polls for responses every minute for the specified timeout period.
        Processes responses and generates counter-offers as needed.

        Args:
            negotiation_id: Negotiation UUID
            timeout_hours: Hours to monitor before concluding
        """
        logger.info(
            "Starting response monitoring",
            negotiation_id=negotiation_id,
            timeout_hours=timeout_hours,
        )

        timeout = datetime.now() + timedelta(hours=timeout_hours)

        while datetime.now() < timeout:
            try:
                # Check for new responses
                await self._process_vendor_responses(negotiation_id)

                # Check if negotiation can be concluded early
                if await self._should_conclude_early(negotiation_id):
                    logger.info(
                        "Concluding negotiation early",
                        negotiation_id=negotiation_id,
                        reason="sufficient_responses",
                    )
                    break

                # Wait before next check
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(
                    "Error in response monitoring",
                    negotiation_id=negotiation_id,
                    error=str(e),
                )

        # Finalize negotiation
        await self._finalize_negotiation(negotiation_id)

        logger.info(
            "Response monitoring completed",
            negotiation_id=negotiation_id,
        )

    async def _process_vendor_responses(
        self,
        negotiation_id: str,
    ) -> None:
        """
        Process new vendor responses

        For each pending response:
        1. Parse response with AI
        2. Extract quoted price
        3. Decide whether to counter-offer
        4. Generate counter-offer if needed

        Args:
            negotiation_id: Negotiation UUID
        """
        # Get pending messages
        query = (
            select(NegotiationVendorMessage)
            .where(
                and_(
                    NegotiationVendorMessage.negotiation_id == negotiation_id,
                    NegotiationVendorMessage.final_status == "pending",
                )
            )
            .options(selectinload(NegotiationVendorMessage.vendor))
        )

        result = await self.db.execute(query)
        pending_messages = result.scalars().all()

        for message in pending_messages:
            try:
                # Simulate response processing
                # In production, this would come from actual vendor responses
                # For now, we'll simulate based on vendor characteristics

                vendor = message.vendor

                # Simulate response rate
                import random
                if random.random() > (vendor.response_rate / 100.0):
                    # Vendor doesn't respond
                    message.final_status = "no_response"
                    continue

                # Simulate quote (random price around target)
                base_price = 50.0  # This would come from the negotiation target
                quoted_price = base_price * (1 + random.uniform(-0.10, 0.15))

                message.response_received = "Simulated quote response"
                message.response_received_at = datetime.now()
                message.quoted_price = round(quoted_price, 2)

                # Decide whether to counter-offer
                target_price = 50.0  # This would come from negotiation
                if quoted_price > target_price * 1.08:
                    # Counter-offer if price is > 8% above target
                    message.counter_offered = True
                    message.final_status = "counter_offered"
                elif quoted_price <= target_price * 1.08:
                    # Accept if price is within 8%
                    message.final_status = "accepted"

                self.db.add(message)

            except Exception as e:
                logger.error(
                    "Failed to process vendor response",
                    message_id=message.id,
                    error=str(e),
                )

        await self.db.commit()

    async def _should_conclude_early(
        self,
        negotiation_id: str,
        min_acceptable_quotes: int = 5,
    ) -> bool:
        """
        Check if negotiation should be concluded early

        Args:
            negotiation_id: Negotiation UUID
            min_acceptable_quotes: Minimum quotes needed to conclude

        Returns:
            True if negotiation can be concluded early
        """
        # Count accepted quotes
        query = (
            select(NegotiationVendorMessage)
            .where(
                and_(
                    NegotiationVendorMessage.negotiation_id == negotiation_id,
                    NegotiationVendorMessage.final_status.in_(["accepted", "no_response"]),
                )
            )
        )

        result = await self.db.execute(query)
        completed_messages = result.scalars().all()

        # Check if we have enough responses or all vendors have responded
        if len(completed_messages) >= min_acceptable_quotes:
            return True

        return False

    async def _finalize_negotiation(
        self,
        negotiation_id: str,
    ) -> None:
        """
        Finalize negotiation and select best quote

        Args:
            negotiation_id: Negotiation UUID
        """
        logger.info(
            "Finalizing negotiation",
            negotiation_id=negotiation_id,
        )

        # Get negotiation with messages
        negotiation = await self.db.get(Negotiation, negotiation_id)
        if not negotiation:
            logger.error("Negotiation not found for finalization", negotiation_id=negotiation_id)
            return

        # Get all quotes
        query = (
            select(NegotiationVendorMessage)
            .where(
                and_(
                    NegotiationVendorMessage.negotiation_id == negotiation_id,
                    NegotiationVendorMessage.quoted_price.isnot(None),
                )
            )
            .options(selectinload(NegotiationVendorMessage.vendor))
        )

        result = await self.db.execute(query)
        quotes = result.scalars().all()

        if not quotes:
            # No quotes received
            negotiation.status = "failed"
            negotiation.closed_at = datetime.now()
            await self.db.commit()

            logger.warning(
                "Negotiation failed - no quotes received",
                negotiation_id=negotiation_id,
            )
            return

        # Find best quote (lowest price)
        best_quote = min(quotes, key=lambda q: q.quoted_price)

        # Calculate savings
        original_price = float(negotiation.target_price) / 0.95  # Reverse the 5% target
        saving_amount = original_price - float(best_quote.quoted_price)
        saving_percent = (saving_amount / original_price) * 100

        # Update negotiation
        negotiation.status = "closed"
        negotiation.closed_at = datetime.now()
        negotiation.winning_vendor_id = best_quote.vendor_id
        negotiation.final_price = float(best_quote.quoted_price)
        negotiation.saving_amount = round(saving_amount, 2)

        # Update vendor message status
        best_quote.final_status = "accepted"

        await self.db.commit()

        logger.info(
            "Negotiation completed",
            negotiation_id=negotiation_id,
            winning_vendor=best_quote.vendor.name,
            final_price=best_quote.quoted_price,
            saving_amount=saving_amount,
        )

    async def get_negotiation_status(
        self,
        negotiation_id: str,
    ) -> dict:
        """
        Get real-time negotiation status

        Args:
            negotiation_id: Negotiation UUID

        Returns:
            Negotiation status with progress and quotes
        """
        try:
            # Get negotiation
            negotiation = await self.db.get(Negotiation, negotiation_id)
            if not negotiation:
                raise ValueError(f"Negotiation not found: {negotiation_id}")

            # Get all vendor messages
            query = (
                select(NegotiationVendorMessage)
                .where(
                    NegotiationVendorMessage.negotiation_id == negotiation_id
                )
                .options(selectinload(NegotiationVendorMessage.vendor))
            )

            result = await self.db.execute(query)
            messages = result.scalars().all()

            # Calculate progress
            total_vendors = len(messages)
            responses_received = sum(
                1 for m in messages if m.response_received_at is not None
            )
            quotes_received = sum(
                1 for m in messages if m.quoted_price is not None
            )
            completion_percentage = (responses_received / total_vendors * 100) if total_vendors > 0 else 0

            # Extract quotes
            quotes = []
            best_quote = None
            best_price = float('inf')

            for message in messages:
                if message.quoted_price is not None:
                    quote_data = {
                        "vendor_id": str(message.vendor_id),
                        "vendor_name": message.vendor.name,
                        "quoted_price": float(message.quoted_price),
                        "response_time": self._calculate_response_time(message),
                        "status": message.final_status,
                    }
                    quotes.append(quote_data)

                    # Track best quote
                    if float(message.quoted_price) < best_price:
                        best_price = float(message.quoted_price)
                        best_quote = quote_data

            # Calculate time remaining
            time_elapsed = (datetime.now() - negotiation.started_at).total_seconds() / 3600
            time_remaining = max(0, 2 - time_elapsed)  # 2-hour window

            return {
                "negotiation_id": str(negotiation.id),
                "status": negotiation.status,
                "commodity": negotiation.commodity,
                "quantity": float(negotiation.quantity),
                "unit": negotiation.unit,
                "target_price": float(negotiation.target_price),
                "progress": {
                    "vendors_contacted": total_vendors,
                    "responses_received": responses_received,
                    "quotes_received": quotes_received,
                    "completion_percentage": round(completion_percentage, 1),
                },
                "quotes": quotes,
                "best_quote": best_quote,
                "time_remaining_hours": round(time_remaining, 1),
                "started_at": negotiation.started_at.isoformat(),
            }

        except Exception as e:
            logger.error("Failed to get negotiation status", error=str(e))
            raise

    def _calculate_response_time(self, message: NegotiationVendorMessage) -> str:
        """
        Calculate human-readable response time

        Args:
            message: Vendor message record

        Returns:
            Formatted response time string
        """
        if message.response_received_at and message.message_sent_at:
            time_diff = (
                message.response_received_at - message.message_sent_at
            ).total_seconds()

            hours = int(time_diff // 3600)
            minutes = int((time_diff % 3600) // 60)

            if hours > 0:
                return f"{hours} hour{'s' if hours != 1 else ''} {minutes} min"
            else:
                return f"{minutes} min"

        return "Not responded"

    async def confirm_order(
        self,
        negotiation_id: str,
        vendor_id: str,
    ) -> dict:
        """
        Confirm order with winning vendor

        Args:
            negotiation_id: Negotiation UUID
            vendor_id: Winning vendor UUID

        Returns:
            Order confirmation details

        Raises:
            ValueError: If confirmation fails
        """
        try:
            # Get negotiation
            negotiation = await self.db.get(Negotiation, negotiation_id)
            if not negotiation:
                raise ValueError(f"Negotiation not found: {negotiation_id}")

            # Get winning vendor
            vendor = await self.db.get(Vendor, vendor_id)
            if not vendor:
                raise ValueError(f"Vendor not found: {vendor_id}")

            # Verify vendor is part of negotiation
            message_query = (
                select(NegotiationVendorMessage)
                .where(
                    and_(
                        NegotiationVendorMessage.negotiation_id == negotiation_id,
                        NegotiationVendorMessage.vendor_id == vendor_id,
                    )
                )
            )

            result = await self.db.execute(message_query)
            vendor_message = result.scalar_one_or_none()

            if not vendor_message:
                raise ValueError("Vendor not part of this negotiation")

            # Calculate savings
            original_amount = float(negotiation.target_price) / 0.95 * float(negotiation.quantity)
            new_amount = float(vendor_message.quoted_price) * float(negotiation.quantity)
            savings = original_amount - new_amount

            return {
                "order_id": str(negotiation.id),
                "negotiation_id": str(negotiation.id),
                "vendor": {
                    "vendor_id": str(vendor.id),
                    "vendor_name": vendor.name,
                    "phone": vendor.phone,
                    "email": f"{vendor.name.lower().replace(' ', '.')}@example.com",
                },
                "order_details": {
                    "commodity": negotiation.commodity,
                    "quantity": float(negotiation.quantity),
                    "unit": negotiation.unit,
                    "confirmed_price": float(vendor_message.quoted_price),
                    "total_amount": round(new_amount, 2),
                },
                "savings": {
                    "original_invoice_amount": round(original_amount, 2),
                    "new_order_amount": round(new_amount, 2),
                    "savings_amount": round(savings, 2),
                    "savings_percent": round((savings / original_amount) * 100, 1),
                },
                "next_steps": [
                    f"Contact {vendor.name} at {vendor.phone} to finalize delivery",
                    f"Share order confirmation: #PROCUREAI-{negotiation.id.hex()[:8].upper()}",
                    "Payment terms as agreed with vendor",
                ],
                "confirmed_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error("Failed to confirm order", error=str(e))
            raise


class CounterOfferEngine:
    """
    Counter-offer generation engine

    Uses AI to generate contextually appropriate counter-offers
    in Hinglish (Hindi+English mix) for Indian business context.
    """

    def __init__(self, ai_client: AIClient):
        """
        Initialize counter-offer engine

        Args:
            ai_client: AI client for message generation
        """
        self.ai_client = ai_client

    async def generate_counter_offer(
        self,
        vendor_name: str,
        quoted_price: float,
        target_price: float,
        counter_price: float,
        commodity: str,
        quantity: float,
        unit: str,
    ) -> str:
        """
        Generate counter-offer message

        Args:
            vendor_name: Vendor name
            quoted_price: Price quoted by vendor
            target_price: Our target price
            counter_price: Our counter-offer price
            commodity: Commodity being negotiated
            quantity: Quantity needed
            unit: Unit of measurement

        Returns:
            Counter-offer message in Hinglish
        """
        prompt = f"""Generate a polite but firm counter-offer message in Hinglish (natural Hindi+English mix used in Indian business):

Context:
- Vendor: {vendor_name}
- They quoted: ₹{quoted_price}/{unit}
- Our target: ₹{target_price}/{unit}
- Our counter-offer: ₹{counter_price}/{unit}
- Quantity: {quantity} {unit}
- Commodity: {commodity}

Requirements:
- Keep it under 100 words
- Be respectful but firm on price
- Mention market competition
- Ask for their best possible price
- Sound natural for Indian business communication

Message:"""

        message = await self.ai_client.call_qwen(
            prompt,
            max_tokens=200,
            temperature=0.7,
        )

        logger.info(
            "Counter-offer generated",
            vendor=vendor_name,
            quoted_price=quoted_price,
            counter_price=counter_price,
            message_length=len(message),
        )

        return message.strip()
