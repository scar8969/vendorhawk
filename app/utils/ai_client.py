"""
AI Client Integration

Provides integration with Qwen3.6 Plus via OpenRouter API
for invoice parsing, intent detection, and message generation.
"""

import asyncio
from typing import Any, Optional

import httpx
from openai import AsyncOpenAI

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AIClient:
    """
    Client for interacting with Qwen3.6 Plus via OpenRouter API

    Handles all AI operations including:
    - Invoice text parsing (OCR output → structured JSON)
    - Intent detection (yes/no/negotiate)
    - Negotiation message generation (Hinglish)
    - Counter-offer response generation
    """

    def __init__(self):
        """Initialize OpenRouter client"""
        if not settings.OPENROUTER_API_KEY:
            logger.warning("OpenRouter API key not configured")

        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
        )
        self.model = settings.QWEN_MODEL

    async def call_qwen(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.3,
        response_format: Optional[dict] = None,
    ) -> str:
        """
        Call Qwen3.6 Plus model via OpenRouter

        Args:
            prompt: Input prompt for the model
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            response_format: Optional response format (e.g., {"type": "json_object"})

        Returns:
            str: Model response text

        Raises:
            Exception: If API call fails after retries
        """
        if not settings.OPENROUTER_API_KEY:
            raise ValueError("OpenRouter API key not configured")

        max_retries = 3
        retry_delay = 1  # seconds

        for attempt in range(max_retries):
            try:
                logger.debug(
                    "Calling Qwen API",
                    model=self.model,
                    max_tokens=max_tokens,
                    attempt=attempt + 1,
                )

                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **({"response_format": response_format} if response_format else {}),
                )

                result = response.choices[0].message.content

                logger.debug(
                    "Qwen API response received",
                    tokens_used=response.usage.total_tokens,
                )

                return result

            except Exception as e:
                logger.warning(
                    "Qwen API call failed",
                    attempt=attempt + 1,
                    error=str(e),
                )

                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error("Qwen API failed after max retries")
                    raise

    async def parse_invoice(self, ocr_text: str) -> dict[str, Any]:
        """
        Parse OCR text into structured invoice data

        Args:
            ocr_text: Raw text extracted from invoice via OCR

        Returns:
            dict: Structured invoice data with fields:
                - vendor_name: str
                - item_name: str
                - item_description: Optional[str]
                - quantity: float
                - unit: str
                - unit_price: float
                - total_amount: float
                - invoice_date: str (ISO format)
                - gstin: Optional[str]

        Raises:
            ValueError: If parsing fails or required fields missing
        """
        prompt = f"""You are an invoice parser. Extract the following information from this invoice text and return ONLY valid JSON:

Invoice Text:
{ocr_text}

Required JSON format:
{{
    "vendor_name": "string",
    "item_name": "string",
    "item_description": "string or null",
    "quantity": number,
    "unit": "string (kg, ton, pieces, etc.)",
    "unit_price": number,
    "total_amount": number,
    "invoice_date": "YYYY-MM-DD",
    "gstin": "string or null"
}}

Extract ONLY the information present in the text. If a field is not found, use null.
Return ONLY the JSON, no other text."""

        try:
            response = await self.call_qwen(
                prompt,
                max_tokens=1000,
                temperature=0.1,  # Low temperature for consistent parsing
                response_format={"type": "json_object"},
            )

            import json

            parsed_data = json.loads(response)

            # Validate required fields
            required_fields = ["vendor_name", "item_name", "quantity", "unit", "unit_price", "total_amount", "invoice_date"]
            missing_fields = [field for field in required_fields if not parsed_data.get(field)]

            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

            logger.info(
                "Invoice parsed successfully",
                vendor=parsed_data["vendor_name"],
                item=parsed_data["item_name"],
            )

            return parsed_data

        except Exception as e:
            logger.error("Invoice parsing failed", error=str(e))
            raise ValueError(f"Failed to parse invoice: {str(e)}")

    async def detect_intent(self, user_message: str) -> str:
        """
        Detect user intent from message

        Args:
            user_message: User's message text

        Returns:
            str: Detected intent - "yes", "no", "negotiate", "question", "cancel"

        Example:
            detect_intent("Yes, please find better vendors") -> "yes"
            detect_intent("No thanks, this price is fine") -> "no"
        """
        prompt = f"""Classify the user's intent from this message. Return ONLY one of these exact words:
- yes (user wants to proceed/start negotiation)
- no (user declines/doesn't want to proceed)
- negotiate (user specifically wants to negotiate)
- question (user is asking for information)
- cancel (user wants to cancel)

User message: "{user_message}"

Intent:"""

        response = await self.call_qwen(
            prompt,
            max_tokens=10,
            temperature=0.1,
        )

        intent = response.strip().lower()

        # Validate intent
        valid_intents = ["yes", "no", "negotiate", "question", "cancel"]
        if intent not in valid_intents:
            logger.warning("Invalid intent detected, defaulting to question", intent=intent)
            return "question"

        logger.debug("Intent detected", intent=intent, message=user_message[:50])
        return intent

    async def generate_negotiation_message(
        self,
        vendor_name: str,
        commodity: str,
        quantity: float,
        unit: str,
        target_price: float,
        factory_name: str = None,
    ) -> str:
        """
        Generate personalized negotiation message for vendor

        Args:
            vendor_name: Name of the vendor
            commodity: Commodity being negotiated
            quantity: Quantity needed
            unit: Unit of measurement
            target_price: Target price per unit
            factory_name: Optional factory name for personalization

        Returns:
            str: Personalized negotiation message in Hinglish (Hindi+English mix)
        """
        prompt = f"""Generate a professional yet friendly WhatsApp message for a vendor negotiation.

Context:
- Vendor: {vendor_name}
- We need: {quantity} {unit} of {commodity}
- Target price: ₹{target_price}/{unit}
- Our company: {factory_name or "a manufacturing company"}

Write in Hinglish (natural mix of Hindi and English as used in Indian business).
Keep it under 100 words.
Be direct but respectful.
Ask for their best quote.

Message:"""

        response = await self.call_qwen(
            prompt,
            max_tokens=200,
            temperature=0.7,  # Higher temperature for more natural messages
        )

        logger.info(
            "Negotiation message generated",
            vendor=vendor_name,
            commodity=commodity,
            message_length=len(response),
        )

        return response.strip()

    async def health_check(self) -> dict:
        """
        Check AI service health

        Returns:
            dict: Health check result
        """
        try:
            # Simple test call
            response = await self.call_qwen("Test", max_tokens=5)
            return {
                "status": "healthy",
                "model": self.model,
                "response_time": 0.5,  # Placeholder
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }


async def check_ai_health() -> dict:
    """
    Check AI service health (standalone function for health checks)

    Returns:
        dict: Health check result
    """
    try:
        client = AIClient()
        return await client.health_check()
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }
