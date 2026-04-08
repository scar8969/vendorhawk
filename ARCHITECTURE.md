# ProcureAI - Complete Architecture Specification

## Document Overview

**Version:** 1.0  
**Last Updated:** 2026-04-08  
**Status:** Detailed Architecture Specification  
**Related Documents:** DESIGN.md (High-level design)

---

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow Architecture](#data-flow-architecture)
4. [API Architecture](#api-architecture)
5. [Database Architecture](#database-architecture)
6. [Security Architecture](#security-architecture)
7. [Deployment Architecture](#deployment-architecture)
8. [Scalability Architecture](#scalability-architecture)
9. [Error Handling Architecture](#error-handling-architecture)
10. [Monitoring & Observability](#monitoring--observability)

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                 │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │         PROGRESSIVE WEB APP (Next.js + React)               │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │   │
│  │  │ Invoice  │ │ Dashboard│ │Negotiation│ │Settings  │      │   │
│  │  │ Capture  │ │          │ │Tracker   │ │          │      │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │   │
│  │                                                              │   │
│  │  State: Zustand | Auth: Supabase | Styling: Tailwind       │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    ↕ HTTPS/WebSocket
┌─────────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              FASTAPI APPLICATION (Railway)                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │   │
│  │  │   Router     │  │Middleware    │  │  Exception   │     │   │
│  │  │              │  │(Auth,CORS,   │  │  Handlers    │     │   │
│  │  │              │  │Rate Limit)   │  │              │     │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    ↕
┌─────────────────────────────────────────────────────────────────────┐
│                       SERVICE LAYER                                   │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │  Invoice        │  │  Price          │  │  Negotiation    │    │
│  │  Processor      │  │  Intelligence   │  │  Engine         │    │
│  │                 │  │                 │  │                 │    │
│  │  - OCR (Tesseract)│  │ - Scrapers     │  │ - Vendor Mgmt   │    │
│  │  - Qwen Parsing │  │ - Cache Logic   │  │ - Message Gen   │    │
│  │  - Validation   │  │ - Price Calc    │  │ - Response Parse│    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│                                                                       │
│  ┌─────────────────┐  ┌─────────────────┐                          │
│  │  Auth Service   │  │  Vendor Service │                          │
│  │                 │  │                 │                          │
│  │  - Supabase     │  │  - Scraping     │                          │
│  │  - JWT Mgmt     │  │  - Scoring      │                          │
│  └─────────────────┘  └─────────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
                                    ↕
┌─────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES LAYER                           │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ OpenRouter   │  │ Supabase     │  │ Web Scrapers │             │
│  │ (Qwen3.6)    │  │ (PostgreSQL) │  │ (Beautiful   │             │
│  │              │  │              │  │  Soup)       │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐                                 │
│  │ Supabase     │  │ Sentry       │                                 │
│  │ Storage      │  │ (Monitoring) │                                 │
│  └──────────────┘  └──────────────┘                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack Matrix

| **Layer** | **Technology** | **Purpose** | **Version** |
|-----------|---------------|-------------|-------------|
| **Frontend** | Next.js | React framework | 14+ |
| | React | UI library | 18+ |
| | Tailwind CSS | Styling | 3.4+ |
| | Zustand | State management | 4.4+ |
| | shadcn/ui | Component library | Latest |
| | next-pwa | PWA capabilities | Latest |
| **Backend** | Python | Runtime | 3.11+ |
| | FastAPI | Web framework | 0.104+ |
| | Pydantic | Validation | 2.5+ |
| | SQLAlchemy | ORM | 2.0+ |
| **AI/ML** | OpenRouter | LLM gateway | Latest |
| | Qwen3.6 Plus | Language model | Latest |
| | Tesseract | OCR engine | 5.3+ |
| **Database** | PostgreSQL | Relational DB | 15+ |
| | Supabase | Backend service | Latest |
| **Infrastructure** | Railway | App hosting | Latest |
| | Vercel | Frontend hosting | Latest |
| | GitHub Actions | CI/CD | Latest |

---

## 2. Component Architecture

### 2.1 Invoice Processing Component

```
┌──────────────────────────────────────────────────────────────┐
│              Invoice Processing Component                     │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Image      │───▶│   OCR        │───▶│    Qwen      │  │
│  │   Upload     │    │   Tesseract  │    │    Parser    │  │
│  │              │    │              │    │              │  │
│  │  - Multipart │    │  - Preprocess│    │  - JSON      │  │
│  │  - Validate  │    │  - Extract   │    │  - Validate  │  │
│  │  - Storage   │    │  - Text      │    │  - Structure │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                   │          │
│         └───────────────────┴───────────────────┘          │
│                             │                              │
│                             ▼                              │
│                    ┌──────────────┐                        │
│                    │   Database   │                        │
│                    │   Storage    │                        │
│                    └──────────────┘                        │
└──────────────────────────────────────────────────────────────┘
```

**Component Details:**

```python
# services/invoice_processor.py

class InvoiceProcessor:
    """
    Orchestrates invoice processing pipeline:
    1. Image upload and validation
    2. OCR text extraction
    3. Qwen-powered parsing
    4. Database storage
    5. Price check trigger
    """
    
    def __init__(self, db: Database, storage: Storage, ai_client: AIClient):
        self.db = db
        self.storage = storage
        self.ai_client = ai_client
        self.ocr_engine = TesseractEngine()
    
    async def process_invoice(
        self, 
        image_file: UploadFile, 
        factory_id: str
    ) -> InvoiceResult:
        # Step 1: Upload image
        image_url = await self.storage.upload_invoice(image_file)
        
        # Step 2: Extract text with OCR
        ocr_text = await self.ocr_engine.extract_text(image_url)
        
        # Step 3: Parse with Qwen
        parsed_data = await self.ai_client.parse_invoice(ocr_text)
        
        # Step 4: Validate and store
        invoice = await self.db.create_invoice(
            factory_id=factory_id,
            parsed_data=parsed_data,
            image_url=image_url
        )
        
        # Step 5: Trigger price check
        await self.trigger_price_check(invoice.id)
        
        return InvoiceResult(invoice=invoice)
```

### 2.2 Price Intelligence Component

```
┌──────────────────────────────────────────────────────────────┐
│              Price Intelligence Component                     │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Commodity   │───▶│   Cache      │───▶│    Price     │  │
│  │  Detector    │    │   Check      │    │    Scrapers  │  │
│  │              │    │              │    │              │  │
│  │  - Mapping   │    │  - Fresh?    │    │  - MCX       │  │
│  │  - NLP       │    │  - TTL 24h   │    │  - Moneycontrol│ │
│  └──────────────┘    └──────────────┘    │  - Agmarknet │  │
│         │                   │          └──────────────┘  │
│         │                   │                   │          │
│         │                   └─────────┬─────────┘          │
│         │                             │                    │
│         ▼                             ▼                    │
│  ┌──────────────┐            ┌──────────────┐             │
│  │   Regional   │            │   Price      │             │
│  │   Adjuster   │            │   Aggregator │             │
│  │              │            │              │             │
│  │  - City      │            │  - Weighted  │             │
│  │    Multiplier│            │    Average   │             │
│  └──────────────┘            └──────────────┘             │
└──────────────────────────────────────────────────────────────┘
```

**Component Details:**

```python
# services/price_intelligence.py

class PriceIntelligence:
    """
    Manages market price intelligence:
    1. Commodity detection from invoice items
    2. Cache management (24h TTL)
    3. Multi-source scraping
    4. Regional price adjustment
    5. Price aggregation
    """
    
    def __init__(self, db: Database, scrapers: List[Scraper]):
        self.db = db
        self.scrapers = scrapers
        self.commodity_mapper = CommodityMapper()
        self.regional_adjuster = RegionalAdjuster()
    
    async def get_market_price(
        self, 
        item_name: str, 
        city: str
    ) -> MarketPrice:
        # Step 1: Detect commodity
        commodity = self.commodity_mapper.map(item_name)
        
        # Step 2: Check cache
        cached = await self.db.get_cached_price(commodity, city)
        if cached and cached.is_fresh():
            return cached
        
        # Step 3: Scrape multiple sources
        prices = []
        for scraper in self.scrapers:
            try:
                price = await scraper.scrape(commodity, city)
                if price:
                    prices.append(price)
            except Exception as e:
                logger.warning(f"Scraper {scraper.name} failed: {e}")
        
        # Step 4: Aggregate prices
        aggregated = self.aggregate_prices(prices)
        
        # Step 5: Apply regional adjustment
        adjusted = self.regional_adjuster.apply(aggregated, city)
        
        # Step 6: Cache result
        await self.db.cache_price(adjusted)
        
        return adjusted
```

### 2.3 Negotiation Engine Component

```
┌──────────────────────────────────────────────────────────────┐
│               Negotiation Engine Component                    │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Intent     │───▶│   Vendor     │───▶│   Message    │  │
│  │   Detector   │    │   Selector   │    │   Generator  │  │
│  │              │    │              │    │              │  │
│  │  - Qwen      │    │  - Rating    │    │  - Qwen      │  │
│  │  - NLP       │    │  - Response  │    │  - Hinglish  │  │
│  │              │    │    Rate      │    │  - Personal  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                   │          │
│         └───────────────────┴───────────────────┘          │
│                             │                              │
│                             ▼                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐│
│  │   Response   │    │   Counter    │    │    Best      ││
│  │   Monitor    │───▶│   Offer      │───▶│    Quote     ││
│  │              │    │   Engine     │    │    Selector  ││
│  │  - 2h Timer  │    │              │    │              ││
│  │  - Polling   │    │  - Qwen      │    │  - Min Price ││
│  │  - Async     │    │  - Logic     │    │  - Confirmed ││
│  └──────────────┘    └──────────────┘    └──────────────┘│
└──────────────────────────────────────────────────────────────┘
```

**Component Details:**

```python
# services/negotiation_engine.py

class NegotiationEngine:
    """
    Orchestrates vendor negotiation:
    1. Intent detection (yes/no/negotiate)
    2. Vendor selection and filtering
    3. Personalized message generation
    4. Response monitoring (2h window)
    5. Counter-offer generation
    6. Best quote selection
    """
    
    def __init__(self, db: Database, ai_client: AIClient, notification_service: NotificationService):
        self.db = db
        self.ai_client = ai_client
        self.notifications = notification_service
        self.message_queue = MessageQueue()
    
    async def start_negotiation(
        self, 
        invoice_id: str,
        factory_id: str
    ) -> Negotiation:
        # Step 1: Get invoice details
        invoice = await self.db.get_invoice(invoice_id)
        
        # Step 2: Select vendors
        vendors = await self.select_vendors(
            commodity=invoice.item_name,
            city=invoice.factory.city,
            limit=50
        )
        
        # Step 3: Create negotiation record
        negotiation = await self.db.create_negotiation(
            invoice_id=invoice_id,
            factory_id=factory_id,
            vendors=vendors
        )
        
        # Step 4: Generate and send messages
        for vendor in vendors:
            message = await self.ai_client.generate_negotiation_message(
                vendor=vendor,
                invoice=invoice
            )
            await self.notifications.send(vendor.phone, message)
            await self.db.log_message(negotiation.id, vendor.id, message)
        
        # Step 5: Start response monitoring
        asyncio.create_task(self.monitor_responses(negotiation.id))
        
        return negotiation
    
    async def monitor_responses(self, negotiation_id: str):
        """Monitor vendor responses for 2 hours"""
        timeout = 2 * 60 * 60  # 2 hours
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout:
            # Check for new responses
            responses = await self.db.get_pending_responses(negotiation_id)
            
            for response in responses:
                await self.process_vendor_response(response)
            
            await asyncio.sleep(60)  # Check every minute
        
        # Select best quote
        await self.finalize_negotiation(negotiation_id)
```

---

## 3. Data Flow Architecture

### 3.1 Invoice Processing Data Flow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  PWA    │───▶│  FastAPI│───▶│ Storage │───▶│ Tesseract│───▶│  Qwen   │
│ Client  │    │  Upload │    │ Service │    │   OCR   │    │  Parser │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
    │              │              │              │              │
    │              │              │              │              │
    │ 1. Capture   │ 2. POST      │ 3. Store     │ 4. Extract  │ 5. Parse
    │    Image     │    /upload    │    Image     │    Text     │    JSON
    │              │              │              │              │
    │              │              │              │              ▼
    │              │              │              │         ┌─────────┐
    │              │              │              │         │ Invoice │
    │              │              │              │         │  JSON   │
    │              │              │              │         └─────────┘
    │              │              │              │              │
    │              │              │              │              │ 6. Store
    │              │              │              │              │    in DB
    │              │              │              │              ▼
    │              │              │              │         ┌─────────┐
    │              │              │              │         │ Database│
    │              │              │              │         │         │
    │              │              │              │         └─────────┘
    │              │              │              │              │
    │              │              │              │              │ 7. Trigger
    │              │              │              │              │   Price
    │              │              │              │              │   Check
    │              │              │              │              ▼
    │              │              │              │         ┌─────────┐
    │              │              │              │         │  Price  │
    │              │              │              │         │Intel   │
    │              │              │              │         └─────────┘
    │              │              │              │              │
    │              │              │              │              │ 8. Return
    │              │              │              │              │   Result
    │              │              │              │              ▼
    │              │              │              │         ┌─────────┐
    │              │              │              │         │   PWA   │
    │              │              │              │         │ Display │
    │              │              │              │         └─────────┘
    │              │              │              │
    ▼              ▼              ▼              ▼
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Display │    │ 200 OK  │    │  Image  │    │  OCR    │
│  Result │    │ + JSON  │    │   URL   │    │  Text   │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

### 3.2 Negotiation Data Flow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  PWA    │───▶│  FastAPI│───▶│ Intent  │───▶│ Vendor  │───▶│ Message │
│ Request │    │ Endpoint│    │ Detector│    │ Selector│    │ Queue   │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
    │              │              │              │              │
    │ 1. "Find     │ 2. POST      │ 3. Qwen     │ 4. Query    │ 5. Queue
    │    Vendors"  │    /negotiate│    Analysis │    DB       │    50
    │              │              │              │              │    msgs
    │              │              │              │              │
    ▼              ▼              ▼              ▼              ▼
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Negotia-│    │ 202     │    │ Intent  │    │  Top 50 │    │Personal-│
│ tion    │    │ Accepted│    │: nego- │    │ Vendors │    │  ized   │
│ Started │    │         │    │   tiate │    │         │    │ Messages│
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                                              │              │
                                              │              │ 6. Send via
                                              │              │    Email/
                                              │              │    Notif
                                              │              ▼
                                              │         ┌─────────┐
                                              │         │ Vendors │
                                              │         │ Receive │
                                              │         └─────────┘
                                              │              │
                                              │              │ 7. Process
                                              │              │    Responses
                                              │              ▼
                                              │         ┌─────────┐
                                              │         │ Response │
                                              │         │ Parser  │
                                              │         └─────────┘
                                              │              │
                                              │              │ 8. Extract
                                              │              │    Quotes
                                              │              ▼
                                              │         ┌─────────┐
                                              │         │ Counter  │
                                              │         │  Offer  │
                                              │         │  Engine │
                                              │         └─────────┘
                                              │              │
                                              │              │ 9. Select
                                              │              │    Best
                                              │              ▼
                                              │         ┌─────────┐
                                              │         │  Best   │
                                              │         │  Quote  │
                                              │         └─────────┘
                                              │              │
                                              │              │ 10. Present
                                              │              │    to User
                                              │              ▼
                                              │         ┌─────────┐
                                              │         │ Factory │
                                              │         │ Owner  │
                                              │         │ Confirm │
                                              │         └─────────┘
                                              │
                                              ▼
                                       ┌─────────┐
                                       │Negotia- │
                                       │tion    │
                                       │Complete│
                                       └─────────┘
```

---

## 4. API Architecture

### 4.1 API Endpoint Specification

#### Invoice Management APIs

```python
# api/invoices.py

from fastapi import APIRouter, UploadFile, Depends
from app.services.invoice_processor import InvoiceProcessor
from app.schemas.invoice import InvoiceResponse, InvoiceUploadResponse

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

@router.post("/upload", response_model=InvoiceUploadResponse)
async def upload_invoice(
    file: UploadFile,
    factory_id: str,
    processor: InvoiceProcessor = Depends()
):
    """
    Upload and process invoice image
    
    Flow:
    1. Validate image file (JPEG/PNG, max 10MB)
    2. Upload to Supabase Storage
    3. Extract text with Tesseract OCR
    4. Parse with Qwen3.6
    5. Store in database
    6. Trigger price check
    7. Return parsed invoice data
    
    Returns: InvoiceUploadResponse with parsed data and price comparison
    """
    result = await processor.process_invoice(file, factory_id)
    return InvoiceUploadResponse(
        invoice_id=result.invoice.id,
        parsed_data=result.parsed_data,
        price_comparison=result.price_comparison,
        processing_time=result.processing_time
    )

@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str):
    """
    Get invoice details by ID
    
    Returns: Complete invoice data with price check and negotiation status
    """
    invoice = await db.get_invoice(invoice_id)
    return InvoiceResponse.from_orm(invoice)

@router.get("/factory/{factory_id}")
async def get_factory_invoices(
    factory_id: str,
    skip: int = 0,
    limit: int = 20
):
    """
    Get paginated list of factory invoices
    
    Returns: List of invoices with pagination metadata
    """
    invoices = await db.get_factory_invoices(factory_id, skip, limit)
    return {
        "invoices": [InvoiceResponse.from_orm(i) for i in invoices],
        "total": len(invoices),
        "page": skip // limit + 1
    }
```

#### Negotiation APIs

```python
# api/negotiations.py

from fastapi import APIRouter, BackgroundTasks
from app.services.negotiation_engine import NegotiationEngine
from app.schemas.negotiation import NegotiationResponse, NegotiationStatus

router = APIRouter(prefix="/api/negotiations", tags=["negotiations"])

@router.post("/start/{invoice_id}", response_model=NegotiationResponse)
async def start_negotiation(
    invoice_id: str,
    background_tasks: BackgroundTasks,
    engine: NegotiationEngine = Depends()
):
    """
    Start vendor negotiation for invoice
    
    Flow:
    1. Validate invoice exists and price check completed
    2. Detect overpayment (> 5%)
    3. Select top 50 vendors by commodity/region
    4. Generate personalized messages with Qwen
    5. Send messages via email/notification
    6. Start background task to monitor responses
    7. Return negotiation tracking ID
    
    Returns: NegotiationResponse with tracking details
    """
    negotiation = await engine.start_negotiation(invoice_id)
    return NegotiationResponse.from_orm(negotiation)

@router.get("/{negotiation_id}", response_model=NegotiationStatus)
async def get_negotiation_status(negotiation_id: str):
    """
    Get real-time negotiation status
    
    Returns: Current status, vendors contacted, responses received, best quote
    """
    status = await engine.get_negotiation_status(negotiation_id)
    return NegotiationStatus(
        negotiation_id=status.id,
        status=status.status,
        vendors_contacted=status.vendors_contacted,
        responses_received=status.responses_received,
        best_quote=status.best_quote,
        time_remaining=status.time_remaining
    )

@router.post("/{negotiation_id}/confirm")
async def confirm_order(negotiation_id: str):
    """
    Confirm order with best quote vendor
    
    Flow:
    1. Validate negotiation is complete
    2. Get best confirmed quote
    3. Calculate savings
    4. Send confirmation to vendor
    5. Update negotiation status
    6. Store savings record
    
    Returns: Confirmation details with savings amount
    """
    result = await engine.confirm_order(negotiation_id)
    return {
        "order_confirmed": True,
        "vendor": result.vendor_name,
        "final_price": result.final_price,
        "savings": result.savings,
        "order_id": result.order_id
    }
```

### 4.2 Request/Response Models

```python
# schemas/invoice.py

from pydantic import BaseModel, Field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

class InvoiceUploadResponse(BaseModel):
    """Response model for invoice upload"""
    invoice_id: str
    parsed_data: 'ParsedInvoiceData'
    price_comparison: 'PriceComparison'
    processing_time: float  # seconds
    
    class Config:
        json_schema_extra = {
            "example": {
                "invoice_id": "123e4567-e89b-12d3-a456-426614174000",
                "parsed_data": {
                    "vendor_name": "ABC Steel Traders",
                    "item_name": "MS Steel Rods",
                    "quantity": 100.0,
                    "unit": "kg",
                    "unit_price": 55.0,
                    "total_amount": 5500.0
                },
                "price_comparison": {
                    "market_price": 50.0,
                    "overpayment_percent": 10.0,
                    "overpayment_amount": 500.0,
                    "recommendation": "negotiate"
                },
                "processing_time": 3.2
            }
        }

class ParsedInvoiceData(BaseModel):
    """Structured invoice data from OCR + Qwen parsing"""
    vendor_name: str = Field(..., description="Vendor name from invoice")
    item_name: str = Field(..., description="Item/product name")
    item_description: Optional[str] = Field(None, description="Detailed description")
    quantity: Decimal = Field(..., gt=0, description="Quantity ordered")
    unit: str = Field(..., description="Unit of measurement (kg, ton, pieces)")
    unit_price: Decimal = Field(..., gt=0, description="Price per unit")
    total_amount: Decimal = Field(..., gt=0, description="Total invoice amount")
    invoice_date: date = Field(..., description="Invoice date")
    gstin: Optional[str] = Field(None, description="GSTIN number")

class PriceComparison(BaseModel):
    """Market price comparison results"""
    market_price: Decimal = Field(..., description="Current market price")
    invoice_price: Decimal = Field(..., description="Price paid on invoice")
    overpayment_percent: Decimal = Field(..., description="Overpayment percentage")
    overpayment_amount: Decimal = Field(..., description="Amount overpaid")
    recommendation: str = Field(..., description="Action recommendation")
    market_source: str = Field(..., description="Source of market price")
    price_freshness: str = Field(..., description="Age of market price data")
```

### 4.3 API Rate Limiting Strategy

```python
# middleware/rate_limit.py

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

# Rate limit tiers
RATE_LIMITS = {
    "free_tier": "10/minute",      # 10 requests per minute
    "standard": "100/minute",      # 100 requests per minute
    "enterprise": "1000/minute",   # 1000 requests per minute
}

# Apply rate limits to endpoints
@app.post("/api/invoices/upload")
@limiter.limit("10/minute")  # Per factory
async def upload_invoice(request: Request):
    pass

@app.get("/api/invoices/{invoice_id}")
@limiter.limit("60/minute")  # Higher limit for reads
async def get_invoice(request: Request, invoice_id: str):
    pass
```

---

## 5. Database Architecture

### 5.1 Entity Relationship Diagram

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  factories  │         │  invoices   │         │ negotiations│
├─────────────┤         ├─────────────┤         ├─────────────┤
│ id (PK)     │────┐    │ id (PK)     │────┐    │ id (PK)     │
│ phone       │    │    │ factory_id  │    │    │ invoice_id  │◄───┐
│ name        │    │    │ vendor_name │    │    │ factory_id  │    │
│ city        │    │    │ item_name   │    │    │ commodity   │    │
│ state       │    │    │ quantity    │    │    │ quantity    │    │
│ materials   │    │    │ unit_price  │    │    │ target_price│    │
└─────────────┘    │    │ status      │    │    │ status      │    │
                   │    └─────────────┘    │    │ winning_    │    │
                   │           │          │    │   vendor_id │    │
                   │           │          │    └─────────────┘    │
                   │           │          │           │          │
                   │           ▼          │           ▼          │
                   │    ┌─────────────┐   │    ┌─────────────┐   │
                   │    │commodity_   │   │    │negotiation_ │   │
                   │    │prices       │   │    │vendor_      │   │
                   │    ├─────────────┤   │    │messages     │   │
                   │    │ id (PK)     │   │    ├─────────────┤   │
                   │    │ commodity   │   │    │ id (PK)     │   │
                   │    │ city        │   │    │ negotiation │   │
                   │    │ price       │   │    │ vendor_id   │   │
                   │    │ source      │   │    │ quoted_price│   │
                   │    │ expires_at  │   │    │ final_status│   │
                   │    └─────────────┘   │    └─────────────┘   │
                   │                      │           │          │
                   │                      │           ▼          │
                   │                      │    ┌─────────────┐   │
                   │                      │    │   vendors   │   │
                   │                      │    ├─────────────┤   │
                   │                      │    │ id (PK)     │◄──┘
                   │                      │    │ name        │
                   │                      │    │ phone       │
                   │                      │    │ city        │
                   │                      │    │ commodities │
                   │                      │    │ rating      │
                   │                      │    │ response_   │
                   │                      │    │   rate      │
                   │                      │    └─────────────┘
                   │                      │
                   └──────────────────────┘
```

### 5.2 Database Indexes Strategy

```sql
-- Performance indexes
CREATE INDEX idx_factories_phone ON factories(phone);
CREATE INDEX idx_invoices_factory_created ON invoices(factory_id, created_at DESC);
CREATE INDEX idx_invoices_status ON invoices(status) WHERE status != 'completed';
CREATE INDEX idx_prices_lookup ON commodity_prices(commodity_code, city, expires_at);
CREATE INDEX idx_negotiations_factory_status ON negotiations(factory_id, status);
CREATE INDEX idx_messages_negotiation ON negotiation_vendor_messages(negotiation_id);

-- JSONB indexes for commodity searches
CREATE INDEX idx_vendors_commodities ON vendors USING GIN(commodities_json);
CREATE INDEX idx_factories_materials ON factories USING GIN(materials_json);

-- Partial indexes for active records
CREATE INDEX idx_active_vendors ON vendors(id) WHERE is_active = true;
CREATE INDEX idx_active_factories ON factories(id) WHERE is_active = true;

-- Composite indexes for common queries
CREATE INDEX idx_negotiation_dashboard ON negotiations(factory_id, started_at DESC) 
WHERE status IN ('active', 'pending');

-- Covering indexes for dashboard queries
CREATE INDEX idx_invoice_dashboard ON invoices(factory_id, created_at DESC, status, total_amount);
```

### 5.3 Database Partitioning Strategy (Future)

```sql
-- Partition invoices by month for better performance
CREATE TABLE invoices_partitioned (
    LIKE invoices INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE invoices_2024_01 PARTITION OF invoices_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE invoices_2024_02 PARTITION OF invoices_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Partition negotiations similarly
CREATE TABLE negotiations_partitioned (
    LIKE negotiations INCLUDING ALL
) PARTITION BY RANGE (started_at);
```

---

## 6. Security Architecture

### 6.1 Authentication & Authorization Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│   PWA    │───▶│ Supabase │───▶│ Supabase │───▶│  FastAPI │───▶│ Protected│
│  Client  │    │   Auth   │    │   JWT    │    │ Middleware│    │  Route   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
    │              │               │               │               │
    │ 1. Enter     │ 2. Send OTP   │ 3. Verify     │ 4. Extract   │ 5. Validate
    │    Phone     │    via SMS    │    + Get JWT  │    User      │    Factory
    │              │               │               │    from JWT  │    Access
    │              │               │               │               │
    ▼              ▼               ▼               ▼               ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ OTP      │    │ User     │    │ JWT      │    │ Factory  │    │ Resource │
│ Input    │    │ Created  │    │ Token    │    │ Context  │    │ Access   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### 6.2 Row Level Security (RLS) Policies

```sql
-- Enable RLS on tables
ALTER TABLE factories ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE negotiations ENABLE ROW LEVEL SECURITY;

-- Policy: Factories can only see their own data
CREATE POLICY factory_isolation ON factories
    FOR ALL
    USING (
        phone = (
            SELECT phone FROM auth.users 
            WHERE id = auth.uid()
        )
    );

-- Policy: Factories can only see their invoices
CREATE POLICY invoice_isolation ON invoices
    FOR ALL
    USING (
        factory_id IN (
            SELECT id FROM factories 
            WHERE phone = (
                SELECT phone FROM auth.users 
                WHERE id = auth.uid()
            )
        )
    );

-- Policy: Admins can see everything
CREATE POLICY admin_full_access ON factories
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM admin_users 
            WHERE user_id = auth.uid()
        )
    );
```

### 6.3 API Security Layers

```python
# middleware/security.py

from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_factory_access(
    credentials: HTTPAuthorizationCredentials = Security(security),
    factory_id: str
):
    """
    Verify factory has access to requested resource
    Implements multi-layer security:
    1. JWT validation
    2. Factory ownership check
    3. Rate limit check
    4. IP reputation check
    """
    # Layer 1: JWT validation
    user = await verify_jwt(credentials.credentials)
    
    # Layer 2: Factory ownership
    factory = await db.get_factory(factory_id)
    if factory.phone != user.phone:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Layer 3: Rate limit check
    if not await rate_limiter.allow_request(user.id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Layer 4: IP reputation (optional)
    if not await ip_reputation.is_safe(request.client.host):
        raise HTTPException(status_code=403, detail="Suspicious activity")
    
    return factory
```

---

## 7. Deployment Architecture

### 7.1 Infrastructure Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      DNS / CloudFlare                       │
│                   procureai.app                             │
└──────────────┬─────────────────────────────┬────────────────┘
               │                             │
               ▼                             ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│      Vercel (PWA)        │    │    Railway (Backend)     │
├──────────────────────────┤    ├──────────────────────────┤
│  ┌────────────────────┐  │    │  ┌────────────────────┐ │
│  │  Next.js Build     │  │    │  │  FastAPI Docker    │ │
│  │  - Static Assets   │  │    │  │  - Auto-scaling    │ │
│  │  - CDN Edge        │  │    │  │  - 1-3 instances   │ │
│  └────────────────────┘  │    │  └────────────────────┘ │
│  ┌────────────────────┐  │    │  ┌────────────────────┐ │
│  │  Edge Functions    │  │    │  │  Environment Vars  │ │
│  │  - Image Opt       │  │    │  │  - Secrets Mgmt    │ │
│  │  - Redirects       │  │    │  └────────────────────┘ │
│  └────────────────────┘  │    │  ┌────────────────────┐ │
└──────────────────────────┘    │  │  Health Checks     │ │
                                │  └────────────────────┘ │
                                └──────────┬───────────────┘
                                           │
              ┌────────────────────────────┼────────────────────────┐
              │                            │                        │
              ▼                            ▼                        ▼
┌────────────────────┐      ┌────────────────────┐    ┌────────────────────┐
│    Supabase        │      │   OpenRouter       │    │    Sentry          │
├────────────────────┤      ├────────────────────┤    ├────────────────────┤
│  ┌──────────────┐  │      │  ┌──────────────┐  │    │  ┌──────────────┐  │
│  │ PostgreSQL   │  │      │  │ Qwen3.6 Plus │  │    │  │ Error Track  │  │
│  │ - Primary DB │  │      │  │ API Gateway  │  │    │  │ Performance  │  │
│  └──────────────┘  │      │  └──────────────┘  │    │  └──────────────┘  │
│  ┌──────────────┐  │      └────────────────────┘    └────────────────────┘
│  │ Auth Service │  │
│  └──────────────┘  │
│  ┌──────────────┐  │
│  │ Storage      │  │
│  │ - Images     │  │
│  └──────────────┘  │
└────────────────────┘
```

### 7.2 CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml

name: Deploy ProcureAI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: |
          pytest --cov=app tests/
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  deploy-backend:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway
        run: |
          railway up --service=procureai-api
      - name: Run migrations
        run: |
          python -m alembic upgrade head

  deploy-frontend:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Vercel
        run: |
          vercel --prod
```

---

## 8. Scalability Architecture

### 8.1 Horizontal Scaling Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer                            │
│                 (Railway built-in)                          │
└──────────────┬──────────────────────────────────────────────┘
               │
               │ Round-robin distribution
               │
    ┌──────────┼──────────┬──────────┐
    │          │          │          │
    ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Instance│ │Instance│ │Instance│ │Instance│
│   1    │ │   2    │ │   3    │ │   N    │
│ FastAPI│ │ FastAPI│ │ FastAPI│ │ FastAPI│
└────────┘ └────────┘ └────────┘ └────────┘
    │          │          │          │
    └──────────┴──────────┴──────────┘
                    │
                    ▼
            ┌───────────────┐
            │  Supabase     │
            │  (Primary DB) │
            └───────────────┘
```

### 8.2 Caching Strategy

```python
# utils/cache.py

from functools import lru_cache
from redis import Redis

class MultiLevelCache:
    """
    Multi-level caching strategy:
    1. In-memory (LRU cache) - fastest, smallest
    2. Redis - fast, shared across instances
    3. Database - persistent source of truth
    """
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        
    @lru_cache(maxsize=1000)
    async def get_commodity_price(self, commodity: str, city: str) -> Optional[float]:
        # Level 1: In-memory cache
        pass
    
    async def get_from_redis(self, key: str) -> Optional[Any]:
        # Level 2: Redis cache
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def get_from_db(self, key: str) -> Optional[Any]:
        # Level 3: Database
        return await self.db.get(key)
    
    async def get(self, key: str) -> Optional[Any]:
        # Try cache levels in order
        if cached := self.get_from_memory(key):
            return cached
        
        if cached := await self.get_from_redis(key):
            return cached
        
        return await self.get_from_db(key)
```

### 8.3 Database Connection Pooling

```python
# utils/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

class DatabaseConnectionPool:
    """
    Database connection pool configuration for scalability
    """
    
    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            database_url,
            pool_size=20,           # Max connections in pool
            max_overflow=10,        # Additional connections under load
            pool_timeout=30,        # Wait time for connection
            pool_recycle=3600,      # Recycle connections after 1 hour
            pool_pre_ping=True,     # Test connections before use
            echo=False
        )
        
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def get_session(self) -> AsyncSession:
        async with self.SessionLocal() as session:
            yield session
```

---

## 9. Error Handling Architecture

### 9.1 Error Classification System

```python
# utils/errors.py

class ProcureAIError(Exception):
    """Base exception for all ProcureAI errors"""
    def __init__(self, message: str, error_code: str, retry_able: bool = False):
        self.message = message
        self.error_code = error_code
        self.retry_able = retry_able
        super().__init__(self.message)

# Error categories
class ValidationError(ProcureAIError):
    """Input validation errors (400)"""
    pass

class AuthenticationError(ProcureAIError):
    """Authentication/authorization errors (401/403)"""
    pass

class NotFoundError(ProcureAIError):
    """Resource not found errors (404)"""
    pass

class BusinessLogicError(ProcureAIError):
    """Business rule violations (422)"""
    pass

class ExternalServiceError(ProcureAIError):
    """External API failures (502/503)"""
    def __init__(self, message: str, service: str):
        super().__init__(message, retry_able=True)
        self.service = service

class DatabaseError(ProcureAIError):
    """Database operation failures (500)"""
    pass
```

### 9.2 Circuit Breaker Pattern

```python
# utils/circuit_breaker.py

from enum import Enum
import asyncio

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, stop trying
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    """
    Circuit breaker for external service calls
    Prevents cascading failures
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        half_open_attempts: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_attempts = half_open_attempts
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
    
    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time and
            (datetime.now() - self.last_failure_time).seconds >= self.timeout
        )
    
    def _on_success(self):
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

---

## 10. Monitoring & Observability

### 10.1 Metrics Collection

```python
# utils/metrics.py

from prometheus_client import Counter, Histogram, Gauge
import time

# Business metrics
invoices_uploaded = Counter(
    'procureai_invoices_uploaded_total',
    'Total invoices uploaded',
    ['factory_id', 'status']
)

price_checks_performed = Counter(
    'procureai_price_checks_total',
    'Total price checks performed',
    ['commodity', 'source']
)

negotiations_started = Counter(
    'procureai_negotiations_started_total',
    'Total negotiations started',
    ['commodity']
)

savings_generated = Gauge(
    'procureai_savings_total',
    'Total savings generated across all factories',
    ['factory_id']
)

# Performance metrics
invoice_processing_time = Histogram(
    'procureai_invoice_processing_seconds',
    'Time spent processing invoices',
    buckets=[1, 2, 5, 10, 15, 30, 60]
)

ocr_accuracy = Gauge(
    'procureai_ocr_accuracy',
    'OCR accuracy rate',
    ['confidence_level']
)

# System metrics
api_request_duration = Histogram(
    'procureapi_request_duration_seconds',
    'API request duration',
    ['endpoint', 'method']
)

external_service_calls = Counter(
    'procureai_external_service_calls_total',
    'External service API calls',
    ['service', 'status']
)
```

### 10.2 Health Check System

```python
# api/health.py

from fastapi import APIRouter
from app.utils.database import database
from app.utils.ai_client import ai_client

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    Monitors: database, external APIs, services
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Database health
    try:
        await database.execute("SELECT 1")
        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time": 0.05  # seconds
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Qwen API health
    try:
        response = await ai_client.health_check()
        health_status["checks"]["ai_service"] = {
            "status": "healthy",
            "model": response.model
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["ai_service"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Tesseract health
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        health_status["checks"]["ocr_service"] = {
            "status": "healthy",
            "version": str(version)
        }
    except Exception as e:
        health_status["checks"]["ocr_service"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    return health_status
```

### 10.3 Logging Strategy

```python
# utils/logger.py

import structlog
from typing import Any

logger = structlog.get_logger()

class StructuredLogger:
    """
    Structured logging for better observability
    """
    
    @staticmethod
    def log_invoice_upload(
        factory_id: str,
        invoice_id: str,
        processing_time: float,
        success: bool,
        error: str = None
    ):
        logger.info(
            "invoice_upload",
            factory_id=factory_id,
            invoice_id=invoice_id,
            processing_time=processing_time,
            success=success,
            error=error,
            timestamp=datetime.now().isoformat()
        )
    
    @staticmethod
    def log_negotiation_start(
        negotiation_id: str,
        invoice_id: str,
        vendors_contacted: int,
        commodity: str
    ):
        logger.info(
            "negotiation_started",
            negotiation_id=negotiation_id,
            invoice_id=invoice_id,
            vendors_contacted=vendors_contacted,
            commodity=commodity,
            timestamp=datetime.now().isoformat()
        )
    
    @staticmethod
    def log_external_api_call(
        service: str,
        endpoint: str,
        status_code: int,
        response_time: float
    ):
        logger.info(
            "external_api_call",
            service=service,
            endpoint=endpoint,
            status_code=status_code,
            response_time=response_time,
            timestamp=datetime.now().isoformat()
        )
```

---

## Appendix A: System Specifications

### A.1 Performance Requirements

| **Metric** | **Target** | **Measurement** |
|------------|------------|-----------------|
| Invoice Processing | < 15 seconds | End-to-end time |
| OCR Accuracy | > 95% | On clear GST invoices |
| API Response Time | < 2 seconds | p95 latency |
| System Uptime | > 99.5% | Monthly availability |
| Database Query | < 500ms | p95 latency |
| Concurrent Users | 50+ | Simultaneous uploads |

### A.2 Scalability Targets

| **Metric** | **Phase 1** | **Phase 2** | **Phase 3** |
|------------|-------------|-------------|-------------|
| Factories | 20 | 100 | 500+ |
| Invoices/Day | 50 | 500 | 5000+ |
| Negotiations/Day | 10 | 100 | 1000+ |
| Storage | 10 GB | 100 GB | 1 TB+ |
| API Calls/Day | 1000 | 10000 | 100000+ |

### A.3 Security Requirements

| **Requirement** | **Implementation** |
|-----------------|-------------------|
| Encryption at Rest | Supabase AES-256 |
| Encryption in Transit | TLS 1.3 |
| Authentication | Supabase Auth (JWT) |
| Authorization | Row-Level Security |
| Audit Logging | All sensitive operations |
| Data Retention | 90 days invoices, 3 years negotiations |
| Compliance | ISO 27001 standards |

---

**Document Status:** Complete  
**Next Steps:** Implementation Phase 1 (Database Schema + FastAPI Setup)  
**Maintainer:** ProcureAI Development Team
