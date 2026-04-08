# Phase 1 Setup Guide

## 🎯 Phase 1: Foundation - Setup Instructions

### Step 1: Supabase Project Setup

1. **Create Supabase Project**
   - Go to https://supabase.com
   - Click "New Project"
   - Choose organization (or create free account)
   - Project name: `procureai`
   - Database password: (choose strong password)
   - Region: Choose closest to India (Singapore)
   - Click "Create new project"

2. **Get Database Credentials**
   - Go to Project Settings → Database
   - Copy the following values:
     - **Database URL**: `postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
     - **Project URL**: `https://[PROJECT-REF].supabase.co`
     - **anon public key**: Found in API settings
     - **service_role key**: Found in API settings

3. **Configure Environment Variables**
   ```bash
   # Copy the environment template
   cp .env.example .env

   # Edit .env file with your Supabase credentials:
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   SUPABASE_URL=https://[PROJECT-REF].supabase.co
   SUPABASE_ANON_KEY=your-anon-key-here
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
   ```

### Step 2: Install Dependencies

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Install Tesseract OCR
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-hin

# macOS:
brew install tesseract tesseract-lang

# Verify Tesseract installation
tesseract --version
```

### Step 3: Configure OpenRouter API

1. **Get OpenRouter API Key**
   - Go to https://openrouter.ai/keys
   - Sign up or login
   - Generate API key (free tier available)

2. **Add to .env**
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-your-key-here
   QWEN_MODEL=qwen/qwen-3.6-plus
   ```

### Step 4: Run Database Migrations

```bash
# Option A: Using Poetry script
poetry run migrate

# Option B: Using Alembic directly
poetry run alembic upgrade head
```

This will create all tables:
- ✅ factories
- ✅ invoices
- ✅ commodity_prices
- ✅ vendors
- ✅ negotiations
- ✅ negotiation_vendor_messages

### Step 5: Seed Test Data

```bash
# Run the seed data script
poetry run python tests/seed_data.py
```

This will populate:
- 10 test factories
- 200 test vendors
- 75 commodity prices (5 sources × 15 city-commodity pairs)
- 50 test invoices

### Step 6: Start Development Server

```bash
# Option A: Using Poetry script
poetry run dev

# Option B: Using Uvicorn directly
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 7: Verify Setup

1. **Check Health Endpoint**
   ```bash
   curl http://localhost:8000/health
   ```

2. **View API Documentation**
   - Open browser: http://localhost:8000/docs
   - Should see FastAPI auto-generated docs

3. **Test Database Connection**
   ```bash
   # Check if tables were created
   poetry run python -c "from app.models import Base; print('Models loaded successfully')"
   ```

## 🔧 Troubleshooting

### Issue: "Module not found" errors
```bash
# Ensure poetry dependencies are installed
poetry install

# If using virtual env, activate it
poetry shell
```

### Issue: Database connection failed
```bash
# Check DATABASE_URL format
# Should be: postgresql://postgres:password@db.project.supabase.co:5432/postgres

# Test connection
poetry run python -c "from app.utils.database import get_engine; print(get_engine())"
```

### Issue: Tesseract not found
```bash
# Check Tesseract installation
which tesseract
tesseract --version

# If not found, install it:
# Ubuntu/Debian: sudo apt-get install tesseract-ocr
# macOS: brew install tesseract
```

### Issue: OpenRouter API key invalid
```bash
# Verify API key format
# Should start with: sk-or-v1-

# Test API connection
poetry run python -c "from app.utils.ai_client import AIClient; client = AIClient(); print('AI client initialized')"
```

## 📊 Verify Database Schema

```bash
# Connect to Supabase database
poetry run python -c "
from app.utils.database import get_db_context
from app.models import Factory
import asyncio

async def check_tables():
    async with get_db_context() as db:
        result = await db.execute('SELECT COUNT(*) FROM factories')
        print(f'Factories: {result.scalar()}')

asyncio.run(check_tables())
"
```

## ✅ Phase 1 Completion Checklist

- [ ] Supabase project created
- [ ] Database credentials configured in .env
- [ ] OpenRouter API key configured
- [ ] Tesseract OCR installed
- [ ] Poetry dependencies installed
- [ ] Database migrations applied
- [ ] Test data seeded
- [ ] Development server starts successfully
- [ ] Health endpoint returns "healthy"
- [ ] Can access API documentation at /docs

## 🚀 Next Steps

Once Phase 1 is complete, you're ready for **Phase 2: Core Invoice Processing**

Phase 2 will implement:
- Invoice upload endpoint
- Tesseract OCR integration
- Qwen AI invoice parsing
- Image preprocessing
- Price check triggering

## 📞 Support

If you encounter issues:
1. Check the logs in the terminal
2. Verify all environment variables are set correctly
3. Ensure Supabase project is active
4. Check Tesseract installation
5. Verify OpenRouter API key is valid

---

**Status:** Phase 1 Foundation Setup
**Estimated Time:** 30-45 minutes
**Difficulty:** Beginner-Friendly
