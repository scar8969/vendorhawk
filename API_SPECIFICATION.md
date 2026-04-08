# ProcureAI - API Specification

## Document Overview

**Version:** 1.0  
**Last Updated:** 2026-04-08  
**Base URL:** `https://api.procureai.app`  
**Authentication:** Bearer Token (JWT from Supabase)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Invoice APIs](#invoice-apis)
3. [Price Intelligence APIs](#price-intelligence-apis)
4. [Negotiation APIs](#negotiation-apis)
5. [Factory Management APIs](#factory-management-apis)
6. [Vendor APIs](#vendor-apis)
7. [Admin APIs](#admin-apis)
8. [Error Responses](#error-responses)
9. [Rate Limiting](#rate-limiting)

---

## Authentication

### Get JWT Token from Supabase

```http
POST https://<project-id>.supabase.co/auth/v1/token?grant_type=password
```

**Request Body:**
```json
{
  "phone": "+919876543210",
  "password": "123456"  // OTP from SMS
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user-id",
    "phone": "+919876543210"
  }
}
```

### Use JWT Token in API Requests

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Invoice APIs

### Upload Invoice

Upload and process invoice image.

```http
POST /api/invoices/upload
```

**Request:** `multipart/form-data`

| **Field** | **Type** | **Required** | **Description** |
|-----------|----------|--------------|-----------------|
| file | File | Yes | Invoice image (JPEG/PNG, max 10MB) |
| factory_id | string | Yes | Factory UUID |

**Response:** `200 OK`
```json
{
  "invoice_id": "123e4567-e89b-12d3-a456-426614174000",
  "parsed_data": {
    "vendor_name": "ABC Steel Traders",
    "item_name": "MS Steel Rods",
    "item_description": "Mild steel rods, 12mm diameter",
    "quantity": "100.00",
    "unit": "kg",
    "unit_price": "55.00",
    "total_amount": "5500.00",
    "invoice_date": "2024-04-08",
    "gstin": "27ABCDE1234F1Z5"
  },
  "price_comparison": {
    "market_price": "50.00",
    "invoice_price": "55.00",
    "overpayment_percent": 10.0,
    "overpayment_amount": "500.00",
    "recommendation": "negotiate",
    "market_source": "MCX",
    "price_freshness": "2 hours ago"
  },
  "processing_time": 3.2,
  "status": "price_check_pending"
}
```

**Error Responses:**

| **Code** | **Description** |
|----------|----------------|
| `400` | Invalid image format or size |
| `413` | File too large (> 10MB) |
| `422` | OCR failed to extract required fields |
| `500` | Internal processing error |

---

### Get Invoice Details

Retrieve complete invoice information.

```http
GET /api/invoices/{invoice_id}
```

**Path Parameters:**

| **Field** | **Type** | **Required** | **Description** |
|-----------|----------|--------------|-----------------|
| invoice_id | string | Yes | Invoice UUID |

**Response:** `200 OK`
```json
{
  "invoice_id": "123e4567-e89b-12d3-a456-426614174000",
  "factory_id": "factory-uuid",
  "parsed_data": {
    "vendor_name": "ABC Steel Traders",
    "item_name": "MS Steel Rods",
    "quantity": "100.00",
    "unit": "kg",
    "unit_price": "55.00",
    "total_amount": "5500.00",
    "invoice_date": "2024-04-08"
  },
  "price_check": {
    "market_price": "50.00",
    "overpayment_percent": 10.0,
    "checked_at": "2024-04-08T10:30:00Z"
  },
  "negotiation": {
    "negotiation_id": "neg-uuid",
    "status": "active",
    "vendors_contacted": 50,
    "responses_received": 12,
    "best_quote": {
      "vendor_name": "XYZ Metals",
      "quoted_price": "48.00",
      "savings": "700.00"
    }
  },
  "created_at": "2024-04-08T10:25:00Z",
  "status": "negotiating"
}
```

---

### Get Factory Invoices

Get paginated list of factory invoices.

```http
GET /api/factories/{factory_id}/invoices
```

**Query Parameters:**

| **Field** | **Type** | **Default** | **Description** |
|-----------|----------|-------------|-----------------|
| skip | integer | 0 | Number of records to skip |
| limit | integer | 20 | Records per page (max 100) |
| status | string | all | Filter by status (processing/parsed/negotiating/completed) |
| from_date | date | null | Filter invoices from this date |
| to_date | date | null | Filter invoices until this date |

**Response:** `200 OK`
```json
{
  "invoices": [
    {
      "invoice_id": "inv-uuid-1",
      "vendor_name": "ABC Steel Traders",
      "item_name": "MS Steel Rods",
      "total_amount": "5500.00",
      "overpayment_percent": 10.0,
      "status": "negotiating",
      "created_at": "2024-04-08T10:25:00Z"
    }
  ],
  "pagination": {
    "total": 45,
    "page": 1,
    "pages": 3,
    "limit": 20
  }
}
```

---

## Price Intelligence APIs

### Trigger Price Check

Manually trigger price check for an invoice.

```http
POST /api/price-check/{invoice_id}
```

**Path Parameters:**

| **Field** | **Type** | **Required** | **Description** |
|-----------|----------|--------------|-----------------|
| invoice_id | string | Yes | Invoice UUID |

**Response:** `200 OK`
```json
{
  "price_check_id": "price-uuid",
  "invoice_id": "inv-uuid",
  "commodity": "STEEL",
  "market_price": "50.00",
  "invoice_price": "55.00",
  "overpayment_percent": 10.0,
  "overpayment_amount": "500.00",
  "recommendation": "negotiate",
  "sources": [
    {
      "name": "MCX",
      "price": "49.50",
      "confidence": 0.95
    },
    {
      "name": "Moneycontrol",
      "price": "50.50",
      "confidence": 0.85
    }
  ],
  "checked_at": "2024-04-08T10:30:00Z",
  "expires_at": "2024-04-09T10:30:00Z"
}
```

---

### Get Current Market Price

Get current market price for a commodity in a city.

```http
GET /api/prices/{commodity_code}/{city}
```

**Path Parameters:**

| **Field** | **Type** | **Required** | **Description** |
|-----------|----------|--------------|-----------------|
| commodity_code | string | Yes | MCX commodity code (STEEL, COPPER, etc.) |
| city | string | Yes | City name |

**Response:** `200 OK`
```json
{
  "commodity_code": "STEEL",
  "city": "Mumbai",
  "price": "50.00",
  "currency": "INR",
  "unit": "kg",
  "sources": [
    {
      "name": "MCX",
      "price": "49.50",
      "fetched_at": "2024-04-08T10:00:00Z"
    },
    {
      "name": "Moneycontrol",
      "price": "50.50",
      "fetched_at": "2024-04-08T10:05:00Z"
    }
  ],
  "aggregation_method": "weighted_average",
  "confidence_score": 0.92,
  "regional_multiplier": 1.02,
  "final_price": "51.00",
  "fetched_at": "2024-04-08T10:30:00Z",
  "expires_at": "2024-04-09T10:30:00Z"
}
```

---

## Negotiation APIs

### Start Negotiation

Initiate vendor negotiation for an invoice.

```http
POST /api/negotiations/start/{invoice_id}
```

**Path Parameters:**

| **Field** | **Type** | **Required** | **Description** |
|-----------|----------|--------------|-----------------|
| invoice_id | string | Yes | Invoice UUID |

**Response:** `202 Accepted`
```json
{
  "negotiation_id": "neg-uuid",
  "invoice_id": "inv-uuid",
  "factory_id": "factory-uuid",
  "commodity": "STEEL",
  "quantity": "100.00",
  "unit": "kg",
  "target_price": "50.00",
  "status": "active",
  "vendors_contacted": 50,
  "estimated_completion": "2024-04-08T12:30:00Z",
  "started_at": "2024-04-08T10:30:00Z"
}
```

---

### Get Negotiation Status

Get real-time negotiation status and progress.

```http
GET /api/negotiations/{negotiation_id}
```

**Path Parameters:**

| **Field** | **Type** | **Required** | **Description** |
|-----------|----------|--------------|-----------------|
| negotiation_id | string | Yes | Negotiation UUID |

**Response:** `200 OK`
```json
{
  "negotiation_id": "neg-uuid",
  "status": "active",
  "progress": {
    "vendors_contacted": 50,
    "responses_received": 12,
    "quotes_received": 8,
    "counter_offers_sent": 3,
    "completion_percentage": 24
  },
  "quotes": [
    {
      "vendor_id": "vendor-uuid-1",
      "vendor_name": "XYZ Metals",
      "quoted_price": "48.00",
      "response_time": "45 minutes",
      "status": "accepted"
    },
    {
      "vendor_id": "vendor-uuid-2",
      "vendor_name": "ABC Traders",
      "quoted_price": "52.00",
      "response_time": "1 hour 20 minutes",
      "status": "counter_offered"
    }
  ],
  "best_quote": {
    "vendor_name": "XYZ Metals",
    "quoted_price": "48.00",
    "savings_vs_invoice": "700.00",
    "savings_percent": 12.7
  },
  "time_remaining": "1 hour 15 minutes",
  "estimated_completion": "2024-04-08T12:30:00Z"
}
```

---

### Confirm Order

Confirm order with the best quote vendor.

```http
POST /api/negotiations/{negotiation_id}/confirm
```

**Path Parameters:**

| **Field** | **Type** | **Required** | **Description** |
|-----------|----------|--------------|-----------------|
| negotiation_id | string | Yes | Negotiation UUID |

**Request Body:**
```json
{
  "vendor_id": "vendor-uuid",
  "confirmed": true
}
```

**Response:** `200 OK`
```json
{
  "order_id": "order-uuid",
  "negotiation_id": "neg-uuid",
  "vendor": {
    "vendor_id": "vendor-uuid",
    "vendor_name": "XYZ Metals",
    "phone": "+919876543210",
    "email": "contact@xyzmetals.com"
  },
  "order_details": {
    "commodity": "STEEL",
    "quantity": "100.00",
    "unit": "kg",
    "confirmed_price": "48.00",
    "total_amount": "4800.00"
  },
  "savings": {
    "original_invoice_amount": "5500.00",
    "new_order_amount": "4800.00",
    "savings_amount": "700.00",
    "savings_percent": 12.7
  },
  "next_steps": [
    "Contact XYZ Metals at +919876543210 to finalize delivery",
    "Share this order confirmation: #PROCUREAI-ORD-12345",
    "Payment terms as agreed with vendor"
  ],
  "confirmed_at": "2024-04-08T12:35:00Z"
}
```

---

## Factory Management APIs

### Complete Factory Onboarding

Complete factory profile after phone verification.

```http
POST /api/factories/onboard
```

**Request Body:**
```json
{
  "factory_name": "Gupta Manufacturing",
  "city": "Ludhiana",
  "state": "Punjab",
  "materials": ["steel", "copper", "aluminium"],
  "udyam_number": "PB02A0000000",
  "monthly_purchase_volume": "500000",
  "primary_contact": "+919876543210"
}
```

**Response:** `201 Created`
```json
{
  "factory_id": "factory-uuid",
  "phone": "+919876543210",
  "name": "Gupta Manufacturing",
  "city": "Ludhiana",
  "state": "Punjab",
  "materials": ["steel", "copper", "aluminium"],
  "udyam_number": "PB02A0000000",
  "onboarded_at": "2024-04-08T10:00:00Z",
  "is_active": true
}
```

---

### Get Factory Dashboard

Get factory dashboard with summary metrics.

```http
GET /api/factories/{factory_id}/dashboard
```

**Path Parameters:**

| **Field** | **Type** | **Required** | **Description** |
|-----------|----------|--------------|-----------------|
| factory_id | string | Yes | Factory UUID |

**Query Parameters:**

| **Field** | **Type** | **Default** | **Description** |
|-----------|----------|-------------|-----------------|
| period | string | month | Time period (week/month/quarter/year) |

**Response:** `200 OK`
```json
{
  "factory": {
    "factory_id": "factory-uuid",
    "name": "Gupta Manufacturing",
    "city": "Ludhiana",
    "member_since": "2024-01-15"
  },
  "summary": {
    "total_savings_this_month": "15000.00",
    "total_savings_all_time": "45000.00",
    "invoices_uploaded_this_month": 12,
    "invoices_uploaded_all_time": 45,
    "negotiations_active": 3,
    "negotiations_completed": 15
  },
  "recent_invoices": [
    {
      "invoice_id": "inv-uuid",
      "item_name": "MS Steel Rods",
      "total_amount": "5500.00",
      "savings": "700.00",
      "status": "completed",
      "created_at": "2024-04-08T10:25:00Z"
    }
  ],
  "active_negotiations": [
    {
      "negotiation_id": "neg-uuid",
      "commodity": "Copper",
      "quantity": "50.00",
      "unit": "kg",
      "status": "active",
      "vendors_contacted": 50,
      "responses_received": 8,
      "best_quote": "450.00",
      "started_at": "2024-04-08T09:00:00Z"
    }
  ],
  "savings_chart": {
    "labels": ["Jan", "Feb", "Mar", "Apr"],
    "data": [5000, 12000, 8000, 15000]
  }
}
```

---

## Vendor APIs

### Register New Vendor

Register a new vendor in the system.

```http
POST /api/vendors/register
```

**Request Body:**
```json
{
  "vendor_name": "XYZ Metals",
  "phone": "+919876543210",
  "email": "contact@xyzmetals.com",
  "city": "Mumbai",
  "state": "Maharashtra",
  "commodities": ["steel", "copper"],
  "business_type": "manufacturer",
  "gst_compliant": true
}
```

**Response:** `201 Created`
```json
{
  "vendor_id": "vendor-uuid",
  "name": "XYZ Metals",
  "phone": "+919876543210",
  "email": "contact@xyzmetals.com",
  "city": "Mumbai",
  "state": "Maharashtra",
  "commodities": ["steel", "copper"],
  "rating": 0.0,
  "total_negotiations": 0,
  "response_rate": 0.0,
  "created_at": "2024-04-08T10:00:00Z"
}
```

---

### Search Vendors

Search vendors by commodity and location.

```http
GET /api/vendors/search
```

**Query Parameters:**

| **Field** | **Type** | **Required** | **Description** |
|-----------|----------|--------------|-----------------|
| commodity | string | Yes | Commodity code |
| city | string | No | City name filter |
| state | string | No | State name filter |
| min_rating | float | No | Minimum rating (0-5) |
| min_response_rate | float | No | Minimum response rate (0-100) |
| limit | integer | No | Max results (default 50) |

**Response:** `200 OK`
```json
{
  "vendors": [
    {
      "vendor_id": "vendor-uuid-1",
      "name": "XYZ Metals",
      "city": "Mumbai",
      "rating": 4.5,
      "response_rate": 85.0,
      "avg_response_hours": 1.2,
      "commodities": ["steel", "copper"]
    }
  ],
  "total": 25,
  "filters_applied": {
    "commodity": "steel",
    "city": "Mumbai",
    "min_rating": 4.0
  }
}
```

---

## Admin APIs

### Get System Metrics

Get system-wide metrics and statistics.

```http
GET /api/admin/metrics
```

**Query Parameters:**

| **Field** | **Type** | **Default** | **Description** |
|-----------|----------|-------------|-----------------|
| period | string | month | Time period (week/month/quarter/year) |

**Response:** `200 OK`
```json
{
  "factories": {
    "total": 150,
    "active": 142,
    "new_this_period": 25,
    "by_state": [
      {"state": "Maharashtra", "count": 45},
      {"state": "Punjab", "count": 38},
      {"state": "Gujarat", "count": 32}
    ]
  },
  "invoices": {
    "total_this_period": 1250,
    "total_all_time": 8500,
    "processing_success_rate": 94.5
  },
  "negotiations": {
    "total_this_period": 350,
    "active": 45,
    "completed": 305,
    "success_rate": 78.0
  },
  "savings": {
    "total_savings_this_period": "450000.00",
    "total_savings_all_time": "1850000.00",
    "average_savings_per_negotiation": "1285.00"
  },
  "performance": {
    "avg_invoice_processing_time": 3.2,
    "avg_negotiation_completion_time": 1.8,
    "ocr_accuracy_rate": 95.2,
    "system_uptime": 99.7
  }
}
```

---

### Health Check

System health check endpoint.

```http
GET /api/admin/health
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2024-04-08T10:30:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time": 0.05,
      "connection_pool": "8/20 used"
    },
    "ai_service": {
      "status": "healthy",
      "model": "qwen-3.6-plus",
      "response_time": 1.2
    },
    "ocr_service": {
      "status": "healthy",
      "version": "5.3.0",
      "available": true
    },
    "storage": {
      "status": "healthy",
      "used_storage": "2.5 GB",
      "available_storage": "97.5 GB"
    }
  }
}
```

---

## Error Responses

### Standard Error Format

All errors follow this format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "file",
      "issue": "File size exceeds 10MB limit"
    },
    "timestamp": "2024-04-08T10:30:00Z",
    "request_id": "req-uuid-12345"
  }
}
```

### Error Codes

| **Code** | **HTTP Status** | **Description** |
|----------|----------------|----------------|
| `VALIDATION_ERROR` | `400` | Invalid input data |
| `UNAUTHORIZED` | `401` | Missing or invalid authentication |
| `FORBIDDEN` | `403` | Insufficient permissions |
| `NOT_FOUND` | `404` | Resource not found |
| `CONFLICT` | `409` | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | `429` | Too many requests |
| `INTERNAL_ERROR` | `500` | Internal server error |
| `SERVICE_UNAVAILABLE` | `503` | External service unavailable |

---

## Rate Limiting

### Rate Limit Tiers

| **Tier** | **Requests/Minute** | **Requests/Hour** |
|----------|---------------------|-------------------|
| Free | 10 | 100 |
| Standard | 100 | 1000 |
| Enterprise | 1000 | 10000 |

### Rate Limit Headers

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1680900000
```

### Rate Limit Error Response

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 100,
      "remaining": 0,
      "resets_at": "2024-04-08T11:00:00Z"
    }
  }
}
```

---

## Webhooks (Future)

### Negotiation Completed Webhook

When a negotiation completes, send webhook to configured URL.

```http
POST {webhook_url}
```

**Payload:**
```json
{
  "event": "negotiation.completed",
  "timestamp": "2024-04-08T12:30:00Z",
  "data": {
    "negotiation_id": "neg-uuid",
    "factory_id": "factory-uuid",
    "commodity": "STEEL",
    "status": "completed",
    "best_quote": {
      "vendor_name": "XYZ Metals",
      "price": "48.00",
      "savings": "700.00"
    }
  }
}
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-04-08  
**API Version:** v1  
**Base URL:** https://api.procureai.app
