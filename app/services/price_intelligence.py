"""
Price Intelligence Service

Manages market price data for commodities through:
1. Multi-source web scraping (MCX, Moneycontrol, Agmarknet)
2. Price caching with 24-hour TTL
3. Regional price adjustments
4. Aggregation from multiple sources
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import CommodityPrice
from app.services.invoice_processor import CommodityMapper
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PriceIntelligence:
    """
    Price intelligence service

    Provides market price data for commodities through
    web scraping and caching strategies.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize price intelligence service

        Args:
            db: Database session for caching
        """
        self.db = db
        self.scrapers = {
            "mcx": MCXScraper(),
            "moneycontrol": MoneycontrolScraper(),
            "agmarknet": AgmarknetScraper(),
        }
        self.regional_adjuster = RegionalAdjuster()

    async def get_market_price(
        self,
        item_name: str,
        city: str,
        invoice_price: Optional[float] = None,
    ) -> dict:
        """
        Get market price for a commodity in a city

        Args:
            item_name: Raw item name from invoice
            city: City name for regional adjustment
            invoice_price: Optional price from invoice for comparison

        Returns:
            dict: Market price data with comparison

        Raises:
            ValueError: If commodity cannot be identified or no price data available
        """
        try:
            # Step 1: Map item name to commodity code
            commodity_code = CommodityMapper.map_to_commodity(item_name)
            if not commodity_code:
                raise ValueError(f"Could not identify commodity for item: {item_name}")

            logger.info(
                "Market price requested",
                item_name=item_name,
                commodity=commodity_code,
                city=city
            )

            # Step 2: Check cache first
            cached_price = await self._get_cached_price(commodity_code, city)
            if cached_price and self._is_fresh(cached_price):
                logger.info("Using cached price", price=cached_price.price)
                return self._build_price_response(
                    cached_price, invoice_price, from_cache=True
                )

            # Step 3: Scrape multiple sources
            prices = await self._scrape_all_sources(commodity_code, city)

            if not prices:
                # Fallback to cached price even if expired
                if cached_price:
                    logger.warning("No live prices, using expired cache")
                    return self._build_price_response(
                        cached_price, invoice_price, from_cache=True, stale=True
                    )
                else:
                    raise ValueError(f"No price data available for {commodity_code} in {city}")

            # Step 4: Aggregate prices
            aggregated_price = self._aggregate_prices(prices)

            # Step 5: Apply regional adjustment
            adjusted_price = await self.regional_adjuster.apply(
                aggregated_price, city
            )

            # Step 6: Cache the result
            await self._cache_price(
                commodity_code, city, adjusted_price
            )

            # Step 7: Build response
            return self._build_price_response(
                adjusted_price, invoice_price, from_cache=False
            )

        except Exception as e:
            logger.error("Failed to get market price", error=str(e))
            raise

    async def _get_cached_price(
        self,
        commodity_code: str,
        city: str,
    ) -> Optional[CommodityPrice]:
        """
        Get cached price from database

        Args:
            commodity_code: MCX commodity code
            city: City name

        Returns:
            Cached CommodityPrice or None
        """
        try:
            # Query for most recent non-expired price
            query = (
                select(CommodityPrice)
                .where(
                    CommodityPrice.commodity_code == commodity_code.upper(),
                    CommodityPrice.city == city,
                    CommodityPrice.expires_at > datetime.now()
                )
                .order_by(CommodityPrice.fetched_at.desc())
                .limit(1)
            )

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.warning("Failed to get cached price", error=str(e))
            return None

    def _is_fresh(self, price_record: CommodityPrice) -> bool:
        """
        Check if cached price is still fresh

        Args:
            price_record: CommodityPrice record

        Returns:
            True if price is still valid
        """
        return price_record.expires_at > datetime.now()

    async def _scrape_all_sources(
        self,
        commodity_code: str,
        city: str,
    ) -> list[dict]:
        """
        Scrape prices from all configured sources

        Args:
            commodity_code: MCX commodity code
            city: City name

        Returns:
            List of price data from successful scrapes
        """
        prices = []

        # Scrape all sources concurrently
        tasks = [
            self._scrape_source(source_name, scraper, commodity_code, city)
            for source_name, scraper in self.scrapers.items()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.warning("Scraper failed", error=str(result))
                continue

            if result:  # Valid price data
                prices.append(result)

        logger.info(
            "Price scraping completed",
            sources_attempted=len(self.scrapers),
            sources_success=len(prices)
        )

        return prices

    async def _scrape_source(
        self,
        source_name: str,
        scraper,
        commodity_code: str,
        city: str,
    ) -> Optional[dict]:
        """
        Scrape price from a single source

        Args:
            source_name: Name of the scraper
            scraper: Scraper instance
            commodity_code: MCX commodity code
            city: City name

        Returns:
            Price data dict or None if scrape fails
        """
        try:
            logger.debug("Scraping price", source=source_name, commodity=commodity_code)

            price_data = await scraper.scrape(commodity_code, city)

            if price_data:
                return {
                    "source": source_name,
                    "price": Decimal(str(price_data["price"])),
                    "confidence": price_data.get("confidence", 0.8),
                    "fetched_at": datetime.now(),
                }

        except Exception as e:
            logger.warning(
                "Scraper failed",
                source=source_name,
                error=str(e)
            )

        return None

    def _aggregate_prices(self, prices: list[dict]) -> dict:
        """
        Aggregate prices from multiple sources

        Uses weighted average based on confidence scores

        Args:
            prices: List of price data from scrapers

        Returns:
            Aggregated price data
        """
        if not prices:
            return {}

        # Calculate weighted average
        total_weight = sum(p["confidence"] for p in prices)
        weighted_price = sum(
            p["price"] * p["confidence"] for p in prices
        ) / total_weight if total_weight > 0 else prices[0]["price"]

        # Calculate average confidence
        avg_confidence = total_weight / len(prices)

        return {
            "price": round(weighted_price, 2),
            "confidence": round(avg_confidence, 2),
            "source_count": len(prices),
            "sources": [p["source"] for p in prices],
        }

    async def _cache_price(
        self,
        commodity_code: str,
        city: str,
        price_data: dict,
    ) -> None:
        """
        Cache price in database

        Args:
            commodity_code: MCX commodity code
            city: City name
            price_data: Price data to cache
        """
        try:
            # Delete old cached prices for this commodity/city
            await self.db.execute(
                delete(CommodityPrice)
                .where(
                    CommodityPrice.commodity_code == commodity_code.upper(),
                    CommodityPrice.city == city,
                )
            )

            # Create new cache entry
            cached_price = CommodityPrice(
                commodity_code=commodity_code.upper(),
                city=city,
                price=price_data["price"],
                source=", ".join(price_data.get("sources", ["unknown"])),
                confidence_score=price_data["confidence"],
                fetched_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=24),
            )

            self.db.add(cached_price)
            await self.db.commit()

            logger.info("Price cached", commodity=commodity_code, city=city, price=price_data["price"])

        except Exception as e:
            logger.error("Failed to cache price", error=str(e))

    def _build_price_response(
        self,
        price_data: dict,
        invoice_price: Optional[float],
        from_cache: bool = False,
        stale: bool = False,
    ) -> dict:
        """
        Build price comparison response

        Args:
            price_data: Market price data
            invoice_price: Optional price from invoice
            from_cache: Whether data is from cache
            stale: Whether cache data is stale

        Returns:
            Formatted price comparison response
        """
        market_price = float(price_data["price"])

        response = {
            "commodity_code": price_data.get("commodity_code", "UNKNOWN"),
            "market_price": market_price,
            "confidence": price_data.get("confidence", 0.8),
            "source": price_data.get("source", "cached"),
            "from_cache": from_cache,
            "stale": stale,
        }

        # Add comparison if invoice price provided
        if invoice_price:
            overpayment_amount = invoice_price - market_price
            overpayment_percent = (overpayment_amount / market_price) * 100 if market_price > 0 else 0

            response.update({
                "invoice_price": invoice_price,
                "overpayment_amount": round(overpayment_amount, 2),
                "overpayment_percent": round(overpayment_percent, 2),
                "recommendation": self._get_recommendation(overpayment_percent),
            })

        return response

    def _get_recommendation(self, overpayment_percent: float) -> str:
        """
        Get recommendation based on overpayment percentage

        Args:
            overpayment_percent: Percentage overpaid

        Returns:
            Recommendation string
        """
        if overpayment_percent > 10:
            return "negotiate"  # Strong recommendation
        elif overpayment_percent > 5:
            return "consider_negotiating"
        else:
            return "fair_price"  # Price is reasonable


class MCXScraper:
    """Scraper for MCX (Multi Commodity Exchange) website"""

    async def scrape(self, commodity_code: str, city: str) -> dict:
        """
        Scrape price from MCX website

        Note: This is a placeholder implementation. In production,
        you would implement actual web scraping or use MCX API.

        Args:
            commodity_code: MCX commodity code
            city: City name (not used for MCX, exchange prices)

        Returns:
            Price data dict
        """
        # Placeholder implementation
        # In production, scrape from https://www.mcxindia.com/
        base_prices = {
            "STEEL": 50.0,
            "COPPER": 750.0,
            "ALUMINIUM": 210.0,
            "CRUDPALMOIL": 55.0,
            "COTTON": 58000.0,
            "CRUDEOIL": 6500.0,
            "ZINC": 250.0,
            "LEAD": 190.0,
            "NICKEL": 1700.0,
            "CARDAMOM": 1200.0,
            "PEPPER": 65000.0,
        }

        base_price = base_prices.get(commodity_code.upper(), 50.0)

        # Add some random variation to simulate live data
        import random
        price = base_price * (1 + random.uniform(-0.05, 0.05))

        return {
            "price": round(price, 2),
            "confidence": 0.95,  # High confidence for exchange data
        }


class MoneycontrolScraper:
    """Scraper for Moneycontrol commodity prices"""

    async def scrape(self, commodity_code: str, city: str) -> dict:
        """
        Scrape price from Moneycontrol

        Note: Placeholder implementation
        """
        # In production, scrape from Moneycontrol website
        import random
        base_price = 50.0  # Placeholder
        price = base_price * (1 + random.uniform(-0.08, 0.08))

        return {
            "price": round(price, 2),
            "confidence": 0.85,  # Medium confidence
        }


class AgmarknetScraper:
    """Scraper for Agmarknet (agricultural commodity prices)"""

    async def scrape(self, commodity_code: str, city: str) -> dict:
        """
        Scrape price from Agmarknet

        Note: Placeholder implementation
        """
        # In production, scrape from Agmarknet website
        import random
        base_price = 50.0  # Placeholder
        price = base_price * (1 + random.uniform(-0.10, 0.10))

        return {
            "price": round(price, 2),
            "confidence": 0.75,  # Lower confidence for mandi prices
        }


class RegionalAdjuster:
    """
    Applies regional price adjustments based on city/location

    Different cities have different price levels due to:
    - Transportation costs
    - Local demand/supply
    - State taxes
    - Market dynamics
    """

    # Regional multipliers for major cities
    # Base: Mumbai = 1.0 (most cities are compared to Mumbai prices)
    CITY_MULTIPLIERS = {
        "Mumbai": 1.0,
        "Delhi": 1.02,
        "Bangalore": 1.03,
        "Chennai": 1.01,
        "Kolkata": 0.98,
        "Hyderabad": 1.02,
        "Pune": 1.01,
        "Ahmedabad": 0.99,
        "Jaipur": 1.04,
        "Ludhiana": 1.05,
        "Surat": 1.0,
        "Nagpur": 1.03,
        "Indore": 1.04,
        "Coimbatore": 1.02,
        "Vadodara": 1.0,
    }

    async def apply(self, price_data: dict, city: str) -> dict:
        """
        Apply regional adjustment to price

        Args:
            price_data: Original price data
            city: City name

        Returns:
            Adjusted price data
        """
        multiplier = self.CITY_MULTIPLIERS.get(city, 1.0)

        adjusted_price = float(price_data["price"]) * multiplier

        return {
            **price_data,
            "price": round(adjusted_price, 2),
            "regional_multiplier": multiplier,
            "city": city,
        }
