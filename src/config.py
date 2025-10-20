"""
Configuration Management

Loads settings from environment variables.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")

    # Model Configuration
    llm_model: str = os.getenv("LLM_MODEL", "gpt-5-mini")  # gpt-5-mini for semantic matching (reasoning), gpt-5-nano for vision (structure)
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")  # openai or anthropic
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # Application Settings
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    database_path: Path = Path(os.getenv("DATABASE_PATH", "data/compliance.db"))

    # Confidence Thresholds
    confidence_high: float = float(os.getenv("CONFIDENCE_HIGH", "0.90"))
    confidence_medium: float = float(os.getenv("CONFIDENCE_MEDIUM", "0.70"))

    # API Retry Configuration
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    retry_delay: float = float(os.getenv("RETRY_DELAY", "1.0"))

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
