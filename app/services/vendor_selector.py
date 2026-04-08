"""
Vendor Selection Service

Intelligently selects and ranks vendors for negotiation based on:
1. Commodity match (must supply the required commodity)
2. Geographic proximity (prefer vendors in same region)
3. Performance metrics (rating, response rate, negotiation history)
4. Availability status (active vendors only)
"""

from typing import List, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Vendor, Negotiation, NegotiationVendorMessage
from app.services.invoice_processor import CommodityMapper
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VendorSelector:
    """
    Vendor selection service

    Selects the best vendors for negotiation based on multiple
    factors including commodity match, location, and performance.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize vendor selector

        Args:
            db: Database session
        """
        self.db = db

    async def select_vendors_for_negotiation(
        self,
        commodity: str,
        city: str,
        state: str,
        quantity: float,
        limit: int = 50,
    ) -> List[Vendor]:
        """
        Select best vendors for negotiation

        Selection Criteria (in order of importance):
        1. Commodity match (must supply the required commodity)
        2. Active status
        3. Geographic proximity (prefer same city/state)
        4. Response rate (prefer vendors who respond)
        5. Rating (prefer highly-rated vendors)
        6. Recent activity (prefer recently active vendors)

        Args:
            commodity: Commodity being negotiated
            city: City for geographic preference
            state: State for geographic preference
            quantity: Quantity needed (for filtering capacity)
            limit: Maximum number of vendors to select

        Returns:
            List of selected vendors, ranked by suitability

        Raises:
            ValueError: If no suitable vendors found
        """
        try:
            logger.info(
                "Selecting vendors for negotiation",
                commodity=commodity,
                city=city,
                limit=limit,
            )

            # Build query with multiple criteria
            query = (
                select(Vendor)
                .where(Vendor.is_active == True)
                .where(Vendor.commodities_json.contains(commodity.lower()))
                .order_by(
                    # Primary: Response rate (most important)
                    Vendor.response_rate.desc(),
                    # Secondary: Rating
                    Vendor.rating.desc(),
                    # Tertiary: Recent activity (newer is better)
                    Vendor.created_at.desc(),
                )
                .limit(limit * 2)  # Get more candidates, then filter
            )

            result = await self.db.execute(query)
            vendors = result.scalars().all()

            if not vendors:
                raise ValueError(
                    f"No active vendors found for commodity: {commodity}"
                )

            # Rank and filter vendors
            ranked_vendors = self._rank_vendors(
                vendors, commodity, city, state
            )

            # Apply geographic preference (boost nearby vendors)
            ranked_vendors = self._apply_geographic_preference(
                ranked_vendors, city, state
            )

            # Filter by capacity and limit
            selected_vendors = ranked_vendors[:limit]

            logger.info(
                "Vendors selected",
                commodity=commodity,
                city=city,
                selected=len(selected_vendors),
                total_candidates=len(vendors),
            )

            return selected_vendors

        except Exception as e:
            logger.error("Vendor selection failed", error=str(e))
            raise

    def _rank_vendors(
        self,
        vendors: List[Vendor],
        commodity: str,
        city: str,
        state: str,
    ) -> List[Vendor]:
        """
        Rank vendors by suitability score

        Scoring Factors:
        - Response rate (40%): Vendors who respond are prioritized
        - Rating (30%): Higher rated vendors preferred
        - Geographic proximity (20%): Nearby vendors preferred
        - Recent negotiations (10%): Active vendors preferred

        Args:
            vendors: List of vendors to rank
            commodity: Required commodity
            city: Target city
            state: Target state

        Returns:
            Ranked list of vendors
        """
        vendor_scores = []

        for vendor in vendors:
            score = 0.0

            # 1. Response rate (0-40 points)
            # Vendors with higher response rates get priority
            response_score = (vendor.response_rate / 100.0) * 40
            score += response_score

            # 2. Rating (0-30 points)
            # Higher rated vendors preferred
            rating_score = (vendor.rating / 5.0) * 30
            score += rating_score

            # 3. Geographic proximity (0-20 points)
            # Prefer vendors in same city, then same state
            if vendor.city == city:
                score += 20  # Same city = highest preference
            elif vendor.state == state:
                score += 10  # Same state = medium preference

            # 4. Recent activity (0-10 points)
            # Vendors with recent negotiations preferred
            if vendor.total_negotiations > 0:
                activity_score = min(10, vendor.total_negotiations) / 10
                score += activity_score

            vendor_scores.append({
                "vendor": vendor,
                "score": score,
                "response_contribution": response_score,
                "rating_contribution": rating_score,
                "geo_contribution": 20 if vendor.city == city else (10 if vendor.state == state else 0),
            })

        # Sort by score (descending)
        vendor_scores.sort(key=lambda x: x["score"], reverse=True)

        # Return ranked vendors
        return [item["vendor"] for item in vendor_scores]

    def _apply_geographic_preference(
        self,
        vendors: List[Vendor],
        target_city: str,
        target_state: str,
    ) -> List[Vendor]:
        """
        Apply geographic preference to vendor ranking

        Boosts vendors from same city/state while maintaining
        overall ranking order.

        Args:
            vendors: List of ranked vendors
            target_city: Target city for preference
            target_state: Target state for preference

        Returns:
            Reordered list with geographic preference
        """
        # Separate vendors by proximity
        same_city = []
        same_state = []
        other = []

        for vendor in vendors:
            if vendor.city == target_city:
                same_city.append(vendor)
            elif vendor.state == target_state:
                same_state.append(vendor)
            else:
                other.append(vendor)

        # Combine with preference: same_city → same_state → other
        # Maintain relative ordering within each group
        return same_city + same_state + other

    async def get_vendor_performance_stats(
        self,
        vendor_id: str,
    ) -> dict:
        """
        Get detailed performance statistics for a vendor

        Args:
            vendor_id: Vendor UUID

        Returns:
            Vendor performance statistics

        Raises:
            ValueError: If vendor not found
        """
        try:
            # Get vendor details
            query = select(Vendor).where(Vendor.id == vendor_id)
            result = await self.db.execute(query)
            vendor = result.scalar_one_or_none()

            if not vendor:
                raise ValueError(f"Vendor not found: {vendor_id}")

            # Get negotiation history
            negotiation_query = (
                select(NegotiationVendorMessage)
                .where(NegotiationVendorMessage.vendor_id == vendor_id)
                .order_by(NegotiationVendorMessage.message_sent_at.desc())
                .limit(50)
            )

            neg_result = await self.db.execute(negotiation_query)
            negotiation_history = neg_result.scalars().all()

            # Calculate statistics
            total_negotiations = len(negotiation_history)
            responses_received = sum(
                1 for msg in negotiation_history if msg.response_received
            )
            quotes_received = sum(
                1 for msg in negotiation_history if msg.quoted_price is not None
            )
            accepted_deals = sum(
                1 for msg in negotiation_history if msg.final_status == "accepted"
            )

            # Calculate average response time
            response_times = []
            for msg in negotiation_history:
                if msg.response_received_at and msg.message_sent_at:
                    time_diff = (
                        msg.response_received_at - msg.message_sent_at
                    ).total_seconds() / 3600  # Convert to hours
                    response_times.append(time_diff)

            avg_response_hours = (
                sum(response_times) / len(response_times)
                if response_times else None
            )

            return {
                "vendor_id": vendor_id,
                "vendor_name": vendor.name,
                "total_negotiations": total_negotiations,
                "responses_received": responses_received,
                "quotes_received": quotes_received,
                "accepted_deals": accepted_deals,
                "response_rate": vendor.response_rate,
                "rating": float(vendor.rating),
                "avg_response_hours": avg_response_hours,
                "recent_performance": self._calculate_recent_performance(
                    negotiation_history
                ),
            }

        except Exception as e:
            logger.error("Failed to get vendor stats", error=str(e))
            raise

    def _calculate_recent_performance(
        self,
        negotiation_history: List[NegotiationVendorMessage],
    ) -> dict:
        """
        Calculate recent performance metrics

        Args:
            negotiation_history: List of negotiation messages

        Returns:
            Recent performance metrics
        """
        if not negotiation_history:
            return {
                "trend": "no_data",
                "improvement": 0.0,
            }

        # Split into recent (last 10) and older
        recent = negotiation_history[:10]
        older = negotiation_history[10:30] if len(negotiation_history) > 10 else []

        # Calculate success rates
        recent_success = sum(
            1 for msg in recent if msg.final_status == "accepted"
        ) / len(recent) if recent else 0

        older_success = sum(
            1 for msg in older if msg.final_status == "accepted"
        ) / len(older) if older else 0

        # Calculate improvement
        improvement = recent_success - older_success

        # Determine trend
        if improvement > 0.1:
            trend = "improving"
        elif improvement < -0.1:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "improvement": round(improvement * 100, 1),  # Percentage
            "recent_success_rate": round(recent_success * 100, 1),
        }


class VendorScorer:
    """
    Vendor scoring and ranking system

    Provides real-time scoring of vendors based on multiple
    performance metrics and negotiation history.
    """

    @staticmethod
    def calculate_vendor_score(vendor: Vendor) -> float:
        """
        Calculate overall vendor score (0-100)

        Score Components:
        - Rating (0-5): 40% weight
        - Response rate (0-100%): 30% weight
        - Negotiation history: 20% weight
        - Recent activity: 10% weight

        Args:
            vendor: Vendor object

        Returns:
            Overall score (0-100)
        """
        score = 0.0

        # Rating component (40%)
        rating_score = (vendor.rating / 5.0) * 40
        score += rating_score

        # Response rate component (30%)
        response_score = (vendor.response_rate / 100.0) * 30
        score += response_score

        # Negotiation history (20%)
        # More negotiations = more experience
        history_score = min(20, vendor.total_negotiations * 2)
        score += history_score

        # Recent activity (10%)
        # Active vendors get bonus
        activity_score = 10 if vendor.total_negotiations > 5 else 0
        score += activity_score

        return round(score, 2)

    @staticmethod
    def calculate_reliability_score(vendor: Vendor) -> float:
        """
        Calculate vendor reliability score (0-100)

        Focuses on consistency and dependability:
        - Response consistency
        - Quote accuracy
        - Deal completion rate

        Args:
            vendor: Vendor object

        Returns:
            Reliability score (0-100)
        """
        # Base score from response rate
        base_score = vendor.response_rate * 0.6

        # Rating indicates reliability
        rating_bonus = (vendor.rating / 5.0) * 40

        # Experience bonus
        experience_bonus = min(20, vendor.total_negotiations) / 2

        return round(base_score + rating_bonus + experience_bonus, 2)
