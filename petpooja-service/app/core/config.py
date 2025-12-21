"""
Configuration Management
Centralized configuration for the entire application
Consolidated from core/config.py and app/config.py
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application configuration settings"""

    # Database Configuration
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "a24_restaurant_dev")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")

    # PetPooja API Configuration
    PETPOOJA_BASE_URL: str = os.getenv("PETPOOJA_BASE_URL", "https://api-v2.petpooja.com")
    PETPOOJA_APP_KEY: str = os.getenv("PETPOOJA_APP_KEY", "")
    PETPOOJA_APP_SECRET: str = os.getenv("PETPOOJA_APP_SECRET", "")
    PETPOOJA_ACCESS_TOKEN: str = os.getenv("PETPOOJA_ACCESS_TOKEN", "")
    PETPOOJA_RESTAURANT_ID: str = os.getenv("PETPOOJA_RESTAURANT_ID", "")
    PETPOOJA_MAPPING_CODE: str = os.getenv("PETPOOJA_MAPPING_CODE", "")

    # PetPooja Sandbox Configuration
    PETPOOJA_SANDBOX_ENABLED: bool = os.getenv("PETPOOJA_SANDBOX_ENABLED", "false").lower() == "true"
    PETPOOJA_SANDBOX_BASE_URL: str = os.getenv(
        "PETPOOJA_SANDBOX_BASE_URL",
        "https://qle1yy2ydc.execute-api.ap-southeast-1.amazonaws.com/V1"
    )
    PETPOOJA_SANDBOX_ORDER_URL: str = os.getenv(
        "PETPOOJA_SANDBOX_ORDER_URL",
        "https://47pfzh5sf2.execute-api.ap-southeast-1.amazonaws.com/V1"
    )
    PETPOOJA_SANDBOX_DASHBOARD_URL: str = os.getenv(
        "PETPOOJA_SANDBOX_DASHBOARD_URL",
        "https://partner.petpooja.com"
    )
    PETPOOJA_SANDBOX_UPDATE_ORDER_URL: str = os.getenv(
        "PETPOOJA_SANDBOX_UPDATE_ORDER_URL",
        "https://qle1yy2ydc.execute-api.ap-southeast-1.amazonaws.com/V1/update_order_status"
    )
    PETPOOJA_SANDBOX_APP_KEY: str = os.getenv("PETPOOJA_SANDBOX_APP_KEY", "")
    PETPOOJA_SANDBOX_APP_SECRET: str = os.getenv("PETPOOJA_SANDBOX_APP_SECRET", "")
    PETPOOJA_SANDBOX_ACCESS_TOKEN: str = os.getenv("PETPOOJA_SANDBOX_ACCESS_TOKEN", "")
    PETPOOJA_SANDBOX_RESTAURANT_ID: str = os.getenv("PETPOOJA_SANDBOX_RESTAURANT_ID", "")

    # AWS Configuration for API Gateway (Sandbox)
    # These credentials are used for AWS Signature Version 4 signing
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-southeast-1")

    # PetPooja API Endpoints
    PETPOOJA_SAVE_ORDER_ENDPOINT: str = os.getenv("PETPOOJA_SAVE_ORDER_ENDPOINT", "/save_order")
    PETPOOJA_FETCH_MENU_ENDPOINT: str = os.getenv("PETPOOJA_FETCH_MENU_ENDPOINT", "/getrestaurantdetails")
    PETPOOJA_FETCH_RESTAURANT_ENDPOINT: str = os.getenv("PETPOOJA_FETCH_RESTAURANT_ENDPOINT", "/getrestaurantdetails")

    # Webhook & Callback Configuration
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")
    PETPOOJA_CALLBACK_URL: str = os.getenv("PETPOOJA_CALLBACK_URL", "https://yourdomain.com/api/petpooja/callback")
    PETPOOJA_WEBHOOK_ENDPOINT: str = os.getenv("PETPOOJA_WEBHOOK_ENDPOINT", "/webhook")

    # Main Backend Integration
    MAIN_BACKEND_URL: str = os.getenv("MAIN_BACKEND_URL", "http://localhost:3000")
    MAIN_BACKEND_API_TOKEN: str = os.getenv("MAIN_BACKEND_API_TOKEN", "a24-backend-secure-token-2024")
    MAIN_BACKEND_WEBHOOK_ENDPOINT: str = os.getenv("MAIN_BACKEND_WEBHOOK_ENDPOINT", "/api/webhooks/petpooja")

    # API Server Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_WORKERS: int = int(os.getenv("API_WORKERS", "4"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "false").lower() == "true"
    API_LOG_LEVEL: str = os.getenv("API_LOG_LEVEL", "info")

    # Application Settings
    APP_NAME: str = os.getenv("APP_NAME", "A24 Restaurant Data Pipeline")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/petpooja_microservice.log")

    # Database Connection Pool Settings (Sync)
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    DB_STATEMENT_TIMEOUT: int = int(os.getenv("DB_STATEMENT_TIMEOUT", "30000"))
    DB_EXECUTOR_MAX_WORKERS: int = int(os.getenv("DB_EXECUTOR_MAX_WORKERS", "2"))

    # Database Connection Pool Settings (Async)
    DB_ASYNC_POOL_SIZE: int = int(os.getenv("DB_ASYNC_POOL_SIZE", "20"))
    DB_ASYNC_MAX_OVERFLOW: int = int(os.getenv("DB_ASYNC_MAX_OVERFLOW", "40"))
    DB_ASYNC_POOL_TIMEOUT: int = int(os.getenv("DB_ASYNC_POOL_TIMEOUT", "30"))
    DB_ASYNC_POOL_RECYCLE: int = int(os.getenv("DB_ASYNC_POOL_RECYCLE", "1800"))

    # API Client Settings
    HTTP_TIMEOUT: int = int(os.getenv("HTTP_TIMEOUT", "30"))
    HTTP_MAX_RETRIES: int = int(os.getenv("HTTP_MAX_RETRIES", "3"))
    HTTP_RETRY_DELAY: int = int(os.getenv("HTTP_RETRY_DELAY", "2"))

    # HTTP Connection Pool Settings
    HTTPX_MAX_KEEPALIVE_CONNECTIONS: int = int(os.getenv("HTTPX_MAX_KEEPALIVE_CONNECTIONS", "20"))
    HTTPX_MAX_CONNECTIONS: int = int(os.getenv("HTTPX_MAX_CONNECTIONS", "100"))

    # Credentials Cache Configuration
    CREDENTIALS_CACHE_TTL_SECONDS: int = int(os.getenv("CREDENTIALS_CACHE_TTL_SECONDS", "300"))

    # Security Settings
    ENCRYPTION_KEY: Optional[str] = os.getenv("ENCRYPTION_KEY", None)
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")  # Comma-separated list
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    # Order Processing Configuration
    ORDER_ID_PREFIX: str = os.getenv("ORDER_ID_PREFIX", "A24-")
    PETPOOJA_ORDER_UDID: str = os.getenv("PETPOOJA_ORDER_UDID", "a24-pipeline")
    PETPOOJA_ORDER_DEVICE_TYPE: str = os.getenv("PETPOOJA_ORDER_DEVICE_TYPE", "Web")
    DEFAULT_PREP_TIME_OFFSET_MINUTES: int = int(os.getenv("DEFAULT_PREP_TIME_OFFSET_MINUTES", "30"))
    MIN_PREP_TIME_MINUTES: int = int(os.getenv("MIN_PREP_TIME_MINUTES", "20"))
    URGENT_ORDER_TIME_MINUTES: int = int(os.getenv("URGENT_ORDER_TIME_MINUTES", "30"))

    @property
    def DATABASE_URL(self) -> str:
        """Get database connection URL (uppercase for compatibility)"""
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def database_url(self) -> str:
        """Get database connection URL (lowercase alias)"""
        return self.DATABASE_URL

    @property
    def petpooja_credentials_configured(self) -> bool:
        """Check if PetPooja credentials are configured"""
        return bool(
            self.PETPOOJA_APP_KEY and
            self.PETPOOJA_APP_SECRET and
            self.PETPOOJA_ACCESS_TOKEN
        )

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from .env


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Legacy compatibility: Direct instance
settings = get_settings()
