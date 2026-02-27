"""
Application Configuration
========================

Centralized configuration management using environment variables.
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )

    # Application
    APP_NAME: str = "Restaurant AI Assistant"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database - PostgreSQL
    DATABASE_URL: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "restaurant_ai"
    DB_USER: str = "admin"
    DB_PASSWORD: str = "admin"

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5

    # Response Caching
    ENABLE_RESPONSE_CACHING: bool = True
    CACHE_TTL_MENU: int = 3600
    CACHE_TTL_RESTAURANT_INFO: int = 86400
    CACHE_TTL_FAQ: int = 86400
    CACHE_TTL_BUSINESS_HOURS: int = 86400
    CACHE_TTL_DEFAULT: int = 1800

    # User Session Cache
    ENABLE_USER_SESSION_CACHE: bool = True
    USER_SESSION_TTL: int = 1800

    # Inventory Cache
    ENABLE_INVENTORY_CACHE: bool = True

    # MongoDB Configuration
    MONGODB_CONNECTION_STRING: str = "mongodb://localhost:27017"
    MONGODB_DATABASE_NAME: str = "restaurant_ai_analytics"
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017

    # OpenAI Base Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL_EMBEDDINGS: str = "text-embedding-ada-002"

    # Purpose-Specific Models
    INTENT_CLASSIFICATION_MODEL: str = "gpt-4o"
    AGENT_MODEL: str = "gpt-4o-mini"
    ENTITY_EXTRACTION_MODEL: str = "gpt-4o-mini"

    # OpenAI Timeouts and Temperature
    OPENAI_TIMEOUT: int = 30
    OPENAI_TEMPERATURE_DEFAULT: float = 0.3
    OPENAI_TEMPERATURE_GREETING: float = 0.7
    OPENAI_TEMPERATURE_ENTITY: float = 0.1
    OPENAI_TEMPERATURE_SUMMARY: float = 0.1

    # Azure OpenAI Configuration (optional alternative to standard OpenAI)
    USE_AZURE_OPENAI: Optional[bool] = False
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_API_VERSION: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT_GPT4O: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI: Optional[str] = None
    AZURE_GPT4O_RPM_LIMIT: Optional[int] = 500
    AZURE_GPT4O_TPM_LIMIT: Optional[int] = 50000
    AZURE_GPT4O_MINI_RPM_LIMIT: Optional[int] = 30000
    AZURE_GPT4O_MINI_TPM_LIMIT: Optional[int] = 2000000
    AZURE_BUFFER_PERCENT: Optional[int] = 80

    # Multi-Account OpenAI Configuration (20 accounts)
    ACCOUNT_1_API_KEY: Optional[str] = None
    ACCOUNT_1_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_1_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_1_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_1_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_1_BUFFER_PERCENT: int = 80

    ACCOUNT_2_API_KEY: Optional[str] = None
    ACCOUNT_2_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_2_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_2_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_2_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_2_BUFFER_PERCENT: int = 80

    ACCOUNT_3_API_KEY: Optional[str] = None
    ACCOUNT_3_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_3_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_3_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_3_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_3_BUFFER_PERCENT: int = 80

    ACCOUNT_4_API_KEY: Optional[str] = None
    ACCOUNT_4_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_4_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_4_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_4_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_4_BUFFER_PERCENT: int = 80

    ACCOUNT_5_API_KEY: Optional[str] = None
    ACCOUNT_5_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_5_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_5_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_5_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_5_BUFFER_PERCENT: int = 80

    ACCOUNT_6_API_KEY: Optional[str] = None
    ACCOUNT_6_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_6_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_6_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_6_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_6_BUFFER_PERCENT: int = 80

    ACCOUNT_7_API_KEY: Optional[str] = None
    ACCOUNT_7_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_7_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_7_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_7_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_7_BUFFER_PERCENT: int = 80

    ACCOUNT_8_API_KEY: Optional[str] = None
    ACCOUNT_8_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_8_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_8_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_8_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_8_BUFFER_PERCENT: int = 80

    ACCOUNT_9_API_KEY: Optional[str] = None
    ACCOUNT_9_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_9_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_9_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_9_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_9_BUFFER_PERCENT: int = 80

    ACCOUNT_10_API_KEY: Optional[str] = None
    ACCOUNT_10_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_10_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_10_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_10_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_10_BUFFER_PERCENT: int = 80

    ACCOUNT_11_API_KEY: Optional[str] = None
    ACCOUNT_11_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_11_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_11_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_11_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_11_BUFFER_PERCENT: int = 80

    ACCOUNT_12_API_KEY: Optional[str] = None
    ACCOUNT_12_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_12_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_12_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_12_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_12_BUFFER_PERCENT: int = 80

    ACCOUNT_13_API_KEY: Optional[str] = None
    ACCOUNT_13_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_13_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_13_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_13_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_13_BUFFER_PERCENT: int = 80

    ACCOUNT_14_API_KEY: Optional[str] = None
    ACCOUNT_14_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_14_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_14_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_14_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_14_BUFFER_PERCENT: int = 80

    ACCOUNT_15_API_KEY: Optional[str] = None
    ACCOUNT_15_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_15_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_15_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_15_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_15_BUFFER_PERCENT: int = 80

    ACCOUNT_16_API_KEY: Optional[str] = None
    ACCOUNT_16_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_16_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_16_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_16_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_16_BUFFER_PERCENT: int = 80

    ACCOUNT_17_API_KEY: Optional[str] = None
    ACCOUNT_17_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_17_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_17_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_17_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_17_BUFFER_PERCENT: int = 80

    ACCOUNT_18_API_KEY: Optional[str] = None
    ACCOUNT_18_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_18_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_18_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_18_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_18_BUFFER_PERCENT: int = 80

    ACCOUNT_19_API_KEY: Optional[str] = None
    ACCOUNT_19_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_19_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_19_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_19_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_19_BUFFER_PERCENT: int = 80

    ACCOUNT_20_API_KEY: Optional[str] = None
    ACCOUNT_20_GPT4O_RPM_LIMIT: int = 500
    ACCOUNT_20_GPT4O_TPM_LIMIT: int = 30000
    ACCOUNT_20_GPT4O_MINI_RPM_LIMIT: int = 500
    ACCOUNT_20_GPT4O_MINI_TPM_LIMIT: int = 200000
    ACCOUNT_20_BUFFER_PERCENT: int = 80

    # LLM Management
    LLM_COOLDOWN_SECONDS: int = 60
    LLM_RETRY_TIMEOUT_SECONDS: int = 300
    LLM_RETRY_POLL_SECONDS: int = 10

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    SECRET_KEY: str
    FRONTEND_URL: str = "http://localhost:3000"
    TIMEZONE: str = "Asia/Kolkata"

    # Payment Configuration
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None
    PAYMENT_TEST_MODE: Optional[bool] = False
    PAYMENT_LINK_EXPIRY_MINUTES: int = 15
    PAYMENT_MAX_RETRY_ATTEMPTS: int = 3
    PAYMENT_STATUS_POLL_INTERVAL_SECONDS: int = 5
    PAYMENT_CURRENCY: str = "INR"
    PAYMENT_TIMEOUT_SECONDS: int = 300
    PAYMENT_SUCCESS_URL: str = "http://localhost:3003/payment/success"
    PAYMENT_FAILURE_URL: str = "http://localhost:3003/payment/failure"
    PAYMENT_CALLBACK_URL: str = "http://localhost:8000/api/v1/payment/callback"
    PAYMENT_WEBHOOK_URL: str = "http://localhost:8000/api/v1/webhook/razorpay"
    PAYMENT_SMS_TEMPLATE: str = "Your order"
    PAYMENT_WHATSAPP_TEMPLATE: str = "payment_link"
    PAYMENT_SUCCESS_MESSAGE: str = "Payment successful! Your order"
    PAYMENT_FAILURE_MESSAGE: str = "Payment failed for order"
    PAYMENT_EXPIRED_MESSAGE: str = "Payment link expired for order"
    PAYMENT_MAX_ATTEMPTS_MESSAGE: str = "Unable to process payment. Please contact the restaurant. Order"

    # Email Configuration
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    SMTP_TIMEOUT: int = 30
    EMAIL_FROM_NAME: str = "Restaurant AI Assistant"
    EMAIL_FROM_ADDRESS: str = "noreply@yourrestaurant.com"
    EMAIL_QUEUE_ENABLED: bool = True
    EMAIL_QUEUE_REDIS_KEY: str = "email:queue"
    EMAIL_QUEUE_BATCH_SIZE: int = 10
    EMAIL_QUEUE_DELAY_SECONDS: float = 1.0
    EMAIL_CIRCUIT_BREAKER_ENABLED: bool = True
    EMAIL_CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    EMAIL_CIRCUIT_BREAKER_TIMEOUT_SECONDS: int = 60
    EMAIL_CIRCUIT_BREAKER_HALF_OPEN_ATTEMPTS: int = 3

    # MSG91 SMS Configuration
    MSG91_API_KEY: Optional[str] = None
    MSG91_SENDER_ID: Optional[str] = None

    # Third Party APIs
    SERPER_API_KEY: Optional[str] = None
    GOOGLE_CSE_ID: Optional[str] = None

    # Notifications (Twilio)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None

    # WhatsApp
    WHATSAPP_API_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_BUSINESS_ACCOUNT_ID: Optional[str] = None
    WHATSAPP_PHONE_NUMBER: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None
    WHATSAPP_WEBHOOK_URL: Optional[str] = None

    # Email (AWS SES)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    SES_FROM_EMAIL: Optional[str] = None

    # Circuit Breakers
    CIRCUIT_BREAKER_OPENAI_FAIL_MAX: int = 5
    CIRCUIT_BREAKER_OPENAI_RESET_TIMEOUT: int = 120
    CIRCUIT_BREAKER_RAZORPAY_FAIL_MAX: int = 5
    CIRCUIT_BREAKER_RAZORPAY_RESET_TIMEOUT: int = 60
    CIRCUIT_BREAKER_TWILIO_FAIL_MAX: int = 3
    CIRCUIT_BREAKER_TWILIO_RESET_TIMEOUT: int = 30
    CIRCUIT_BREAKER_WHATSAPP_FAIL_MAX: int = 3
    CIRCUIT_BREAKER_WHATSAPP_RESET_TIMEOUT: int = 30

    # CORS Configuration
    ALLOWED_ORIGINS: str = "*"
    ALLOWED_METHODS: str = "GET,POST,PUT,DELETE,PATCH,OPTIONS"
    ALLOWED_HEADERS: str = "*"

    # Session Configuration
    SESSION_TIMEOUT_MINUTES: int = 60
    CONVERSATION_TIMEOUT_MINUTES: int = 30

    # Waiter Configuration
    WAITER_NAMES: str = "Nesamani,Priya,Arjun,Meera,Ravi,Divya,Karthik,Anjali,Vikram,Lakshmi,Rajesh,Pooja,Arun,Nisha,Suresh,Deepa,Rohan,Kavya,Aditya,Sana"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # File Upload
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: str = "jpg,jpeg,png,pdf,txt"

    # CrewAI Agent
    USE_CREWAI_AGENT: bool = True

    # Test/Load Testing Configuration
    TEST_OTP_ENABLED: bool = True  # Enable constant OTP for testing
    TEST_OTP_CODE: str = "123456"  # Constant OTP code for load testing
    AUTH_REQUIRED: bool = True     # Require authentication before chat

    # Sticky Routing (Pin sessions to specific API accounts for consistency)
    ENABLE_STICKY_ROUTING: bool = False

    # Voice Activity Detection (VAD) Settings
    VAD_ENGINE: str = "silero"  # silero, ten, or webrtc
    VAD_SPEECH_THRESHOLD: float = 0.6  # Probability above which speech is detected
    VAD_SILENCE_THRESHOLD: float = 0.3  # Probability below which silence is detected
    VAD_SILENCE_FRAMES: int = 60  # Consecutive silent frames (~2 seconds) before ending speech

    # Logging
    LOG_LEVEL: str = "INFO"

    # Backward compatibility properties
    @property
    def PRIMARY_LLM_MODEL(self) -> str:
        """Legacy alias for AGENT_MODEL"""
        return self.AGENT_MODEL

    @property
    def waiter_names_list(self) -> list[str]:
        """Get waiter names as a list (parsed from comma-separated string)"""
        if isinstance(self.WAITER_NAMES, list):
            return self.WAITER_NAMES
        return [name.strip() for name in self.WAITER_NAMES.split(',') if name.strip()]


# Global settings instance
settings = Settings()

# Backward compatibility alias (migrated from app.utils.config)
config = settings


def get_settings() -> Settings:
    """Get application settings"""
    return settings
