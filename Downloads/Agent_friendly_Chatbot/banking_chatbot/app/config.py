"""
Configuration management for Banking Chatbot.
Handles environment variables and application settings.
"""
from typing import Optional, Literal
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Banking Chatbot API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # API Keys
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")

    # Database
    database_url: str = Field(
        "sqlite+aiosqlite:///./banking_chatbot.db",
        env="DATABASE_URL"
    )

    # Redis (for caching and rate limiting)
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")

    # LLM Settings
    default_model: str = Field("claude-sonnet-4-20250514", env="DEFAULT_MODEL")
    fallback_model: str = Field("claude-haiku-4-20250514", env="FALLBACK_MODEL")
    max_tokens: int = Field(150, env="MAX_TOKENS")
    temperature: float = Field(0.0, env="TEMPERATURE")

    # Routing Settings
    confidence_threshold: float = Field(0.7, env="CONFIDENCE_THRESHOLD")
    escalation_threshold: float = Field(0.4, env="ESCALATION_THRESHOLD")
    max_retries: int = Field(2, env="MAX_RETRIES")

    # Rate Limiting
    rate_limit_requests: int = Field(100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(60, env="RATE_LIMIT_WINDOW")

    # Human Escalation
    escalation_email: Optional[str] = Field(None, env="ESCALATION_EMAIL")
    escalation_webhook: Optional[str] = Field(None, env="ESCALATION_WEBHOOK")

    # Analytics
    enable_analytics: bool = Field(True, env="ENABLE_ANALYTICS")
    analytics_retention_days: int = Field(90, env="ANALYTICS_RETENTION_DAYS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance
settings = get_settings()
