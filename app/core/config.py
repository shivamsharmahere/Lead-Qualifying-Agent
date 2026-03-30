from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Groq API Configuration
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "groq/llama-3.1-70b-versatile"

    # Database Configuration
    DATABASE_URL: str = (
        "postgresql+asyncpg://admin:secretpassword@localhost:5432/leadbot_db"
    )

    # Follow-up Configuration
    FOLLOW_UP_INACTIVITY_MINUTES: int = 30
    FOLLOW_UP_MAX_COUNT: int = 3

    # Chat Context
    MAX_CONTEXT_MESSAGES: int = 20

    # Scoring Thresholds
    HIGH_PRIORITY_BUDGET_INR: float = 7000000.0
    HIGH_PRIORITY_TIMELINE_MONTHS: int = 3

    # API & General
    API_RATE_LIMIT_PER_MIN: int = 60
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached Settings instance.
    Settings is loaded once at startup and cached for the lifetime of the application.
    """
    return Settings()
