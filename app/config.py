"""
Application Configuration

Environment-based configuration management using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""

from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings

    Loads configuration from environment variables with validation.
    All sensitive values should be loaded from environment, not hardcoded.
    """

    # App Settings
    APP_ENV: str = Field(default="development", description="Application environment")
    APP_VERSION: str = "0.1.0"
    BASE_URL: str = Field(default="http://localhost:8000", description="Base API URL")
    SECRET_KEY: str = Field(default="change-this-secret-key-in-production", description="Secret key for JWT")

    # Database
    DATABASE_URL: str = Field(default="postgresql://user:password@localhost:5432/procureai", description="Database connection URL")
    SUPABASE_URL: str = Field(default="", description="Supabase project URL")
    SUPABASE_ANON_KEY: str = Field(default="", description="Supabase anonymous key")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="", description="Supabase service role key")

    # AI/LLM
    OPENROUTER_API_KEY: str = Field(default="", description="OpenRouter API key")
    QWEN_MODEL: str = Field(default="qwen/qwen-3.6-plus", description="Qwen model name")

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )

    # Scraping
    SCRAPER_USER_AGENT: str = Field(default="ProcureAI/1.0", description="User agent for web scraping")
    SCRAPER_RATE_LIMIT: int = Field(default=2, description="Rate limit for scraping (requests per second)")

    # Storage
    SUPABASE_STORAGE_URL: str = Field(default="", description="Supabase storage URL")
    SUPABASE_STORAGE_BUCKET: str = Field(default="procureai-invoices", description="Supabase storage bucket name")

    # OCR
    TESSERACT_PATH: str = Field(default="/usr/bin/tesseract", description="Path to Tesseract OCR executable")
    TESSERACT_LANG: str = Field(default="eng+hin", description="Tesseract language(s)")

    # Rate Limiting
    RATE_LIMIT_FREE: str = Field(default="10/minute", description="Rate limit for free tier")
    RATE_LIMIT_STANDARD: str = Field(default="100/minute", description="Rate limit for standard tier")
    RATE_LIMIT_ENTERPRISE: str = Field(default="1000/minute", description="Rate limit for enterprise tier")

    # Cache (Redis)
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    CACHE_TTL: int = Field(default=86400, description="Cache TTL in seconds (24 hours)")

    # Monitoring
    SENTRY_DSN: str = Field(default="", description="Sentry DSN for error tracking")
    ENABLE_DEBUG_LOGGING: bool = Field(default=True, description="Enable debug logging")

    # Model Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v):
        """Validate database URL format"""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must start with postgresql:// or postgresql+asyncpg://")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.APP_ENV == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance

    Returns:
        Settings: Cached application settings
    """
    return Settings()


# Export settings instance
settings = get_settings()
