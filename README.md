# ProcureAI — AI-Powered Procurement Agent for Indian MSMEs

> Stop losing margins to vendors. AI negotiates on WhatsApp.

ProcureAI is an AI-powered procurement agent that helps Indian MSME manufacturers cut raw-material costs by **18%** through automated price checking and autonomous vendor negotiation.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?logo=nextdotjs&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## 🎯 Problem

Indian MSMEs lose **₹4 lakh crore annually** because they:
- Buy from fragmented vendors at inflated prices
- Never compare prices across suppliers
- Never negotiate effectively
- Lack market price visibility

## 💡 Solution

ProcureAI is a **PWA-based AI agent** that:
1. **Scans invoice photos** via mobile camera
2. **Checks prices** against live market rates
3. **Negotiates autonomously** with vendors
4. **Delivers savings** directly to the bottom line

## ✨ Features

- **Invoice OCR Scanning** – Tesseract-powered extraction from GST invoices
- **Live Price Checking** – multi-source market data
- **Autonomous Negotiation** – contacts vendors in parallel
- **Real-time Tracking** – monitor negotiation progress
- **Savings Dashboard** – track money saved over time
- **Vendor Database** – verified vendor registry
- **Regional Pricing** – city-specific price adjustments

## 🛠 Tech Stack

**Backend**
- Python 3.11+ · FastAPI · SQLAlchemy · Alembic
- Qwen3.6 Plus via OpenRouter · Tesseract OCR
- PostgreSQL (Supabase) · Redis · Celery

**Frontend**
- Next.js 14 PWA · React 18 · Tailwind CSS + shadcn/ui
- Zustand · Supabase Auth (phone OTP)

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ · PostgreSQL 15+ · Tesseract OCR · Node.js 18+

```bash
git clone git@github.com:scar8969/vendorhawk.git
cd vendorhawk

# Backend
poetry install
cp .env.example .env        # set DATABASE_URL, OPENROUTER_API_KEY, Supabase creds
poetry run migrate
poetry run dev              # http://localhost:8000
```

### Tesseract OCR
- **Ubuntu/Debian:** `sudo apt-get install tesseract-ocr tesseract-ocr-hin`
- **macOS:** `brew install tesseract tesseract-lang`
- **Windows:** install from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)

## 🏗 Project Structure

```
vendorhawk/
├── app/                    # FastAPI application
│   ├── api/                # API routers (invoices, vendors, negotiations…)
│   ├── services/           # Business logic (OCR, negotiation, pricing…)
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── utils/              # AI client, OCR client, database, logging
│   └── main.py             # Application entry
├── tests/                  # Test suites
├── alembic/                # Database migrations
├── DESIGN.md               # Product design
├── ARCHITECTURE.md         # Technical architecture
├── API_SPECIFICATION.md    # API documentation
└── pyproject.toml          # Python dependencies
```

## 🧪 Development

```bash
poetry run test             # run tests with coverage
poetry run black app/ tests/   # format
poetry run ruff check app/ tests/  # lint
poetry run mypy app/        # type check
poetry run alembic revision --autogenerate -m "desc"   # new migration
poetry run alembic upgrade head                          # apply migrations
```

## 📚 Documentation

- [DESIGN.md](DESIGN.md) — product design & requirements
- [ARCHITECTURE.md](ARCHITECTURE.md) — technical architecture
- [API_SPECIFICATION.md](API_SPECIFICATION.md) — API reference
- [PHASE1_SETUP.md](PHASE1_SETUP.md) · [PHASE2_IMPLEMENTATION.md](PHASE2_IMPLEMENTATION.md) · [PHASE3_IMPLEMENTATION.md](PHASE3_IMPLEMENTATION.md) — build phases

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

*Stop losing money. Start negotiating with AI.*