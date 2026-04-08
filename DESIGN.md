# ProcureAI - Complete Design Document

## Executive Summary

**Product:** AI-powered procurement agent for Indian MSME manufacturers
**Platform:** Progressive Web App (PWA)
**Core Value:** Reduce procurement costs by 18% through AI-driven price checking and vendor negotiation
**Revenue Model:** Free during MVP (future: 2% of verified savings)
**Target:** 20 factories in 3 months → 500+ in year 1

---

## Problem Statement

Indian MSMEs lose **₹4 lakh crore annually** (18% margins) because:
- Buy raw materials from fragmented vendors at inflated prices
- Never compare prices across vendors
- Never negotiate effectively
- Lack market price visibility

---

## Solution Overview

ProcureAI is a PWA-based AI agent that:
1. **Scans invoice photos** via mobile camera
2. **Checks prices** against live market rates
3. **Negotiates autonomously** with 50+ vendors
4. **Delivers savings** directly to the bottom line

---

## Technology Stack

### Backend
- **Framework:** Python 3.11+ / FastAPI
- **Architecture:** Modular monolith (microservices later)
- **AI/LLM:** Qwen3.6 Plus via OpenRouter (free tier)
- **OCR:** Tesseract (open-source)
- **Database:** PostgreSQL (Supabase hosted)
- **Auth:** Supabase Auth (phone OTP)
- **Hosting:** Railway or Render

### Frontend
- **Framework:** Next.js 14 (App Router) + React 18
- **Styling:** Tailwind CSS + shadcn/ui
- **State:** Zustand or React Context
- **PWA:** next-pwa plugin
- **Hosting:** Vercel

### External Services
- **Price Data:** Multi-source scraping (MCX, Moneycontrol, Agmarknet)
- **Vendor Data:** IndiaMART, TradeIndia scraping
- **Monitoring:** Sentry (error tracking)
- **CI/CD:** GitHub Actions

---

## Core User Flows

### Flow 1: Invoice Scanning
1. Factory owner opens PWA, taps "Upload Invoice"
2. Captures photo via mobile camera
3. Image uploaded to FastAPI
4. Tesseract OCR extracts text
5. Qwen3.6 parses text → structured JSON
6. Invoice saved to database
7. Price check triggered automatically
8. Factory owner sees price comparison

### Flow 2: Price Checking
1. Commodity detected from invoice item
2. Check cache for fresh market price (<24 hours)
3. If cache miss, scrape multiple sources
4. Apply regional price multiplier
5. Calculate overpayment percentage
6. Alert factory owner if overpayment > 5%

### Flow 3: Vendor Negotiation
1. Factory owner requests negotiation ("Find better vendors")
2. Query vendor database for commodity/region
3. Select top 50 vendors (by response rate, rating)
4. Qwen generates personalized messages (Hinglish)
5. Send messages via PWA notifications/email
6. Monitor responses for 2 hours
7. Parse vendor quotes with Qwen
8. Generate counter-offers if needed
9. Select best confirmed quote
10. Present to factory owner for confirmation

### Flow 4: Factory Onboarding
1. New user opens PWA
2. Enter phone number
3. Receive OTP (Supabase Auth)
4. Complete profile: factory name, city, materials
5. Dashboard opens with welcome message

---

## Database Schema

### Core Tables

**factories**
```sql
CREATE TABLE factories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(15) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    udyam_number VARCHAR(20),
    materials_json JSONB NOT NULL,
    onboarded_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_factories_phone ON factories(phone);
```

**invoices**
```sql
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    factory_id UUID REFERENCES factories(id),
    vendor_name VARCHAR(255) NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    item_description TEXT,
    quantity DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL,
    invoice_date DATE NOT NULL,
    gstin VARCHAR(15),
    raw_ocr_text TEXT,
    parsed_json JSONB NOT NULL,
    image_url TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'processing',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_invoices_factory ON invoices(factory_id, created_at DESC);
```

**commodity_prices**
```sql
CREATE TABLE commodity_prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commodity_code VARCHAR(20) NOT NULL,
    city VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    source VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(3, 2) NOT NULL,
    fetched_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_prices_lookup ON commodity_prices(commodity_code, city, expires_at);
```

**vendors**
```sql
CREATE TABLE vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    commodities_json JSONB NOT NULL,
    rating DECIMAL(3, 2) DEFAULT 0.0,
    total_negotiations INTEGER DEFAULT 0,
    avg_response_hours DECIMAL(5, 2),
    response_rate DECIMAL(5, 2) DEFAULT 0.0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_vendors_location ON vendors(city, state);
CREATE INDEX idx_vendors_commodities ON vendors USING GIN(commodities_json);
```

**negotiations**
```sql
CREATE TABLE negotiations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID REFERENCES invoices(id),
    factory_id UUID REFERENCES factories(id),
    commodity VARCHAR(50) NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    target_price DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP,
    winning_vendor_id UUID REFERENCES vendors(id),
    final_price DECIMAL(10, 2),
    saving_amount DECIMAL(12, 2)
);

CREATE INDEX idx_negotiations_factory ON negotiations(factory_id, status);
```

**negotiation_vendor_messages**
```sql
CREATE TABLE negotiation_vendor_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    negotiation_id UUID REFERENCES negotiations(id),
    vendor_id UUID REFERENCES vendors(id),
    message_sent TEXT NOT NULL,
    message_sent_at TIMESTAMP DEFAULT NOW(),
    response_received TEXT,
    response_received_at TIMESTAMP,
    quoted_price DECIMAL(10, 2),
    counter_offered BOOLEAN DEFAULT false,
    final_status VARCHAR(20) DEFAULT 'pending'
);

CREATE INDEX idx_messages_negotiation ON negotiation_vendor_messages(negotiation_id);
```

---

## API Endpoints

### Invoice Management
- `POST /api/invoices/upload` - Upload and process invoice
- `GET /api/invoices/{invoice_id}` - Get invoice details
- `GET /api/factories/{factory_id}/invoices` - List factory invoices

### Price Intelligence
- `POST /api/price-check/{invoice_id}` - Trigger price check
- `GET /api/prices/{commodity_code}/{city}` - Get current market price

### Negotiation
- `POST /api/negotiations/start/{invoice_id}` - Start negotiation
- `GET /api/negotiations/{negotiation_id}` - Get negotiation status
- `POST /api/negotiations/{negotiation_id}/confirm` - Confirm best quote

### Factory Management
- `POST /api/factories/onboard` - Complete factory profile
- `GET /api/factories/{factory_id}/dashboard` - Get dashboard data

### Vendor Management
- `POST /api/vendors/register` - Register new vendor
- `GET /api/vendors/search` - Search vendors by commodity/location

### Admin
- `GET /api/admin/metrics` - System-wide metrics
- `GET /api/admin/health` - Health check status

---

## Project Structure

```
procureai/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Environment configuration
│   ├── api/
│   │   ├── invoices.py
│   │   ├── negotiations.py
│   │   ├── factories.py
│   │   ├── vendors.py
│   │   └── admin.py
│   ├── services/
│   │   ├── invoice_processor.py    # OCR + Qwen parsing
│   │   ├── price_intelligence.py   # Scraping + pricing
│   │   ├── negotiation_engine.py   # Vendor negotiation
│   │   └── auth_service.py         # Supabase auth
│   ├── models/
│   │   ├── factory.py
│   │   ├── invoice.py
│   │   ├── vendor.py
│   │   └── negotiation.py
│   ├── schemas/
│   │   ├── invoice.py
│   │   ├── negotiation.py
│   │   └── factory.py
│   └── utils/
│       ├── ai_client.py            # OpenRouter + Qwen
│       ├── ocr_client.py           # Tesseract wrapper
│       ├── scraper.py              # Web scraping utilities
│       └── validators.py           # Input validation
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── pwa/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── public/
├── .env.example
├── pyproject.toml
└── README.md
```

---

## Implementation Phases (12 Weeks)

### Phase 1: Foundation (Week 1-2)
1. Database schema + Supabase setup
2. FastAPI project structure
3. Environment configuration
4. Seed test data

### Phase 2: Core Invoice Processing (Week 3-4)
3. Invoice OCR + Qwen parsing
4. MCX price check integration

### Phase 3: Vendor & Negotiation (Week 5-6)
5. Vendor DB seed + management
6. Negotiation engine

### Phase 4: PWA Frontend (Week 7-8)
7. Next.js PWA setup
8. Core PWA features

### Phase 5: Testing & Refinement (Week 9-10)
9. Testing suite
10. Error handling & edge cases

### Phase 6: Deployment & Launch (Week 11-12)
11. Production deployment
12. End-to-end testing

---

## Security & Compliance

### ISO 27001 Standards
- Encryption at rest (Supabase)
- Encryption in transit (TLS 1.3)
- Audit logging for all operations
- Role-based access control
- Data retention policies (90 days invoices, 3 years negotiations)
- Vendor opt-out mechanism

### Input Validation
- Pydantic schemas for API validation
- SQL injection prevention (SQLAlchemy ORM)
- XSS prevention (React escaping)
- File upload validation

### API Security
- CORS restrictions
- Rate limiting per user
- API key rotation
- Dependency scanning (Dependabot)

---

## Error Handling Strategy

### Invoice Processing
- Image quality checks
- OCR retry logic (3 attempts)
- Fallback to manual entry
- User-friendly error messages

### Price Intelligence
- Multi-source fallback
- Cache with disclaimers
- Graceful degradation
- Admin alerts on failures

### Negotiation Engine
- Vendor response monitoring
- Low response rate alerts
- Timeout handling (2 hours)
- Fallback to best available

### External Services
- Retry logic with exponential backoff
- Circuit breakers for failing services
- Health check endpoints
- Graceful degradation

---

## Testing Strategy

### Unit Tests (Pytest)
- OCR processing accuracy
- Qwen prompt validation
- Commodity mapping logic
- Price calculation accuracy

### Integration Tests
- Full invoice processing flow
- Price check with scrapers
- Negotiation state machine
- Database operations

### E2E Tests (Playwright)
- Invoice upload flow
- Dashboard navigation
- Negotiation tracking
- Savings visualization

### Performance Tests
- Concurrent invoice uploads (10+)
- Scraper response times
- Database query performance
- API response times (<15s target)

---

## Success Metrics

### Technical
- 95% OCR accuracy on clear GST invoices
- <15s response time for invoice processing
- 80%+ scraper success rate
- 99.5% system uptime

### Business
- 20 factories in 3 months
- 500+ factories in year 1
- 18% average savings per invoice
- 60%+ user retention (3 months)

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://...
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# AI/LLM
OPENROUTER_API_KEY=sk-or-v1-...
QWEN_MODEL=qwen/qwen-3.6-plus

# App Settings
APP_ENV=production
BASE_URL=https://procureai.app
CORS_ORIGINS=https://procureai.app

# Scraping
SCRAPER_USER_AGENT=ProcureAI/1.0
SCRAPER_RATE_LIMIT=2

# Monitoring (Optional)
SENTRY_DSN=https://...
```

---

## Key Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| OCR accuracy on poor invoices | Image preprocessing, request clearer photos |
| Scraper reliability | Multi-source fallback, caching |
| Vendor response rates | Vendor scoring, prefer responsive vendors |
| Qwen3.6 availability | Monitor OpenRouter status |
| Scraping legal issues | Respect robots.txt, vendor opt-out |
| Data privacy | ISO 27001 compliance, encryption |

---

## Future Enhancements

### Post-MVP
- Payment integration (2% fee collection)
- WhatsApp Business API integration
- Multi-language support (Hindi, Tamil, etc.)
- Advanced analytics dashboard
- Mobile apps (iOS, Android)
- Vendor management portal
- Commodity price alerts
- Batch invoice processing
- ERP integration

---

## Decision Log

All design decisions documented in separate decision records for traceability and future reference.

---

**Document Version:** 1.0
**Last Updated:** 2026-04-08
**Status:** Ready for Implementation
