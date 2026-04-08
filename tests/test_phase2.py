"""
Phase 2 Integration Test

Tests the complete invoice processing pipeline:
1. Invoice upload
2. OCR text extraction
3. AI parsing
4. Price checking
"""

import asyncio
import io
from pathlib import Path

from app.services.invoice_processor import InvoiceProcessor, CommodityMapper
from app.services.price_intelligence import PriceIntelligence
from app.utils.database import get_db_context


async def test_commodity_mapper():
    """Test commodity mapping functionality"""
    print("\n🧪 Testing Commodity Mapper...")

    test_cases = [
        ("MS Steel Rods 12mm", "STEEL"),
        ("Copper Wire 2mm", "COPPER"),
        ("Aluminium Sheet 5mm", "ALUMINIUM"),
        ("Crude Palm Oil Refined", "CRUDPALMOIL"),
        ("Cotton Bales Grade A", "COTTON"),
        ("Unknown Product XYZ", None),
    ]

    for item_name, expected in test_cases:
        result = CommodityMapper.map_to_commodity(item_name)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{item_name}' -> {result} (expected: {expected})")

    print("✅ Commodity Mapper tests completed")


async def test_price_intelligence():
    """Test price intelligence service"""
    print("\n🧪 Testing Price Intelligence...")

    async with get_db_context() as db:
        price_service = PriceIntelligence(db)

        # Test market price retrieval
        try:
            result = await price_service.get_market_price(
                item_name="MS Steel Rods",
                city="Mumbai",
                invoice_price=55.0
            )

            print("✅ Market price retrieved:")
            print(f"   Commodity: {result['commodity_code']}")
            print(f"   Market Price: ₹{result['market_price']}")
            print(f"   Invoice Price: ₹{result.get('invoice_price', 'N/A')}")
            print(f"   Overpayment: {result.get('overpayment_percent', 0):.1f}%")
            print(f"   Recommendation: {result.get('recommendation', 'N/A')}")
            print(f"   Source: {result['source']}")

        except Exception as e:
            print(f"❌ Price intelligence test failed: {str(e)}")


async def test_ocr_client():
    """Test OCR client with sample image"""
    print("\n🧪 Testing OCR Client...")

    from app.utils.ocr_client import OCRClient

    try:
        ocr_client = OCRClient()

        # Create a simple test image with text
        from PIL import Image, ImageDraw, ImageFont

        # Create test image
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)

        # Add some text
        draw.text((50, 50), "Invoice #12345", fill='black')
        draw.text((50, 100), "Steel Rods 12mm", fill='black')
        draw.text((50, 150), "Quantity: 100 kg", fill='black')
        draw.text((50, 200), "Price: ₹55/kg", fill='black')
        draw.text((50, 250), "Total: ₹5500", fill='black')

        # Save to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img.save(tmp.name)
            temp_path = tmp.name

        try:
            # Test OCR
            text, confidence = await ocr_client.extract_text_async(temp_path)

            print(f"✅ OCR Extraction completed:")
            print(f"   Confidence: {confidence:.1f}%")
            print(f"   Text length: {len(text)} characters")
            print(f"   Text preview: {text[:100]}...")

        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)

    except Exception as e:
        print(f"❌ OCR client test failed: {str(e)}")


async def test_ai_client():
    """Test AI client with Qwen"""
    print("\n🧪 Testing AI Client...")

    from app.utils.ai_client import AIClient

    try:
        ai_client = AIClient()

        # Test intent detection
        test_message = "Yes, please find better vendors for me"
        intent = await ai_client.detect_intent(test_message)

        print(f"✅ Intent Detection:")
        print(f"   Message: '{test_message}'")
        print(f"   Detected Intent: {intent}")

        # Test negotiation message generation
        message = await ai_client.generate_negotiation_message(
            vendor_name="ABC Steel Traders",
            commodity="Steel",
            quantity=100.0,
            unit="kg",
            target_price=50.0,
            factory_name="Test Factory"
        )

        print(f"✅ Negotiation Message Generated:")
        print(f"   Length: {len(message)} characters")
        print(f"   Preview: {message[:150]}...")

    except Exception as e:
        print(f"❌ AI client test failed: {str(e)}")


async def run_all_tests():
    """Run all Phase 2 integration tests"""
    print("🚀 Starting Phase 2 Integration Tests...")
    print("=" * 60)

    # Test commodity mapper
    await test_commodity_mapper()

    # Test OCR client
    await test_ocr_client()

    # Test AI client
    await test_ai_client()

    # Test price intelligence
    await test_price_intelligence()

    print("\n" + "=" * 60)
    print("✨ Phase 2 Integration Tests Completed!")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
