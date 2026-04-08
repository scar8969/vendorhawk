"""
Seed Data Script

Populates the database with initial test data for development and testing.
"""

import asyncio
from datetime import datetime, timedelta
from random import choice, randint, uniform
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Factory, Invoice, Vendor, CommodityPrice


# Test data constants
CITIES = [
    ("Mumbai", "Maharashtra"),
    ("Delhi", "Delhi"),
    ("Bangalore", "Karnataka"),
    ("Chennai", "Tamil Nadu"),
    ("Kolkata", "West Bengal"),
    ("Hyderabad", "Telangana"),
    ("Pune", "Maharashtra"),
    ("Ahmedabad", "Gujarat"),
    ("Jaipur", "Rajasthan"),
    ("Ludhiana", "Punjab"),
]

COMMODITIES = ["steel", "copper", "aluminium", "crude palm oil", "cotton"]

MATERIALS_OPTIONS = [
    ["steel", "copper", "aluminium"],
    ["steel", "aluminium"],
    ["copper", "brass"],
    ["steel", "iron"],
    ["aluminium", "zinc"],
]

VENDOR_NAMES = [
    "ABC Steel Traders", "XYZ Metals", "Prime Suppliers",
    "Global Materials", "National Distributors", "City Wholesale",
    "Quality Steels", "Metro Metals", "Elite Suppliers", "Fast Traders",
]

COMMODITY_CODES = {
    "steel": "STEEL",
    "copper": "COPPER",
    "aluminium": "ALUMINIUM",
    "crude palm oil": "CRUDPALMOIL",
    "cotton": "COTTON",
}


async def seed_factories(db: AsyncSession, count: int = 10) -> list[Factory]:
    """
    Seed test factories

    Args:
        db: Database session
        count: Number of factories to create

    Returns:
        List of created factories
    """
    factories = []

    for i in range(count):
        city, state = choice(CITIES)
        materials = choice(MATERIALS_OPTIONS)

        factory = Factory(
            phone=f"+91{randint(7000000000, 9999999999)}",
            name=f"Test Factory {i+1}",
            city=city,
            state=state,
            udyam_number=f"{''.join(choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(5))}{randint(100000, 999999)}",
            materials_json=materials,
            is_active=True,
        )

        db.add(factory)
        factories.append(factory)

    await db.commit()
    print(f"✅ Seeded {count} factories")
    return factories


async def seed_vendors(db: AsyncSession, count: int = 200) -> list[Vendor]:
    """
    Seed test vendors

    Args:
        db: Database session
        count: Number of vendors to create

    Returns:
        List of created vendors
    """
    vendors = []

    for i in range(count):
        city, state = choice(CITIES)
        # Ensure each vendor supplies at least one commodity
        num_commodities = randint(1, 3)
        commodities = choice(COMMODITIES_OPTIONS)[:num_commodities]

        vendor = Vendor(
            name=f"{choice(VENDOR_NAMES)} {i+1}",
            phone=f"+91{randint(7000000000, 9999999999)}",
            city=city,
            state=state,
            commodities_json=commodities,
            rating=round(uniform(3.5, 5.0), 1),
            total_negotiations=randint(0, 50),
            avg_response_hours=round(uniform(0.5, 4.0), 1),
            response_rate=round(uniform(20.0, 95.0), 1),
            is_active=True,
        )

        db.add(vendor)
        vendors.append(vendor)

    await db.commit()
    print(f"✅ Seeded {count} vendors")
    return vendors


async def seed_commodity_prices(db: AsyncSession) -> list[CommodityPrice]:
    """
    Seed test commodity prices

    Args:
        db: Database session

    Returns:
        List of created commodity prices
    """
    prices = []

    # Create prices for each commodity in major cities
    for commodity in COMMODITIES:
        commodity_code = COMMODITY_CODES[commodity]

        for city, _ in CITIES[:5]:  # Top 5 cities
            # Create multiple price sources
            for source in ["MCX", "Moneycontrol", "Agmarknet"]:
                price = round(uniform(40.0, 100.0), 2)

                commodity_price = CommodityPrice(
                    commodity_code=commodity_code,
                    city=city,
                    price=price,
                    source=source,
                    confidence_score=round(uniform(0.7, 0.95), 2),
                    expires_at=datetime.now() + timedelta(hours=24),
                )

                db.add(commodity_price)
                prices.append(commodity_price)

    await db.commit()
    print(f"✅ Seeded {len(prices)} commodity prices")
    return prices


async def seed_invoices(db: AsyncSession, factories: list[Factory], count: int = 50) -> list[Invoice]:
    """
    Seed test invoices

    Args:
        db: Database session
        factories: List of factories to create invoices for
        count: Number of invoices per factory

    Returns:
        List of created invoices
    """
    invoices = []

    for factory in factories:
        for _ in range(count):
            commodity = choice(COMMODITIES)

            invoice = Invoice(
                factory_id=factory.id,
                vendor_name=choice(VENDOR_NAMES),
                item_name=f"{commodity.capitalize()} Grade A",
                item_description=f"High quality {commodity} for industrial use",
                quantity=round(uniform(50.0, 500.0), 2),
                unit="kg",
                unit_price=round(uniform(40.0, 100.0), 2),
                total_amount=round(uniform(2000.0, 50000.0), 2),
                invoice_date=datetime.now() - timedelta(days=randint(1, 90)),
                gstin=f"27ABCDE1234F1Z5",
                parsed_json={
                    "vendor_name": choice(VENDOR_NAMES),
                    "item_name": f"{commodity.capitalize()} Grade A",
                    "quantity": 100.0,
                    "unit": "kg",
                    "unit_price": 55.0,
                },
                image_url=f"https://storage.example.com/invoices/{uuid4()}.jpg",
                status=choice(["processing", "parsed", "price_checked", "completed"]),
            )

            db.add(invoice)
            invoices.append(invoice)

    await db.commit()
    print(f"✅ Seeded {len(invoices)} invoices across {len(factories)} factories")
    return invoices


async def seed_all_data(db: AsyncSession) -> dict:
    """
    Seed all test data

    Args:
        db: Database session

    Returns:
        Dictionary with counts of seeded data
    """
    print("🌱 Starting database seeding...")

    # Seed in correct order due to foreign key constraints
    factories = await seed_factories(db, count=10)
    vendors = await seed_vendors(db, count=200)
    commodity_prices = await seed_commodity_prices(db)
    invoices = await seed_invoices(db, factories, count=5)

    print(f"✨ Database seeding completed!")
    print(f"   - 10 factories")
    print(f"   - 200 vendors")
    print(f"   - {len(commodity_prices)} commodity prices")
    print(f"   - {len(invoices)} invoices")

    return {
        "factories": len(factories),
        "vendors": len(vendors),
        "commodity_prices": len(commodity_prices),
        "invoices": len(invoices),
    }


if __name__ == "__main__":
    # Run seeding directly
    import asyncio

    from app.utils.database import get_db_context

    async def main():
        async with get_db_context() as db:
            await seed_all_data(db)

    asyncio.run(main())
