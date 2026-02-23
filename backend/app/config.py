from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

# .env lives at the project root (one level above backend/)
_env_file = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    # App
    environment: str = "development"
    base_url: str = "http://localhost:8000"
    debug: bool = True

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""

    # OpenAI
    openai_api_key: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    database_url: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Email (Resend)
    resend_api_key: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Admin
    admin_api_key: str = "dev-admin-key"

    # CORS (comma-separated origins for production)
    allowed_origins: str = ""

    # Email sender (must be verified in Resend)
    email_from_address: str = "CallHook <notifications@callhook.com>"

    # Subscription cost for ROI calculation
    subscription_cost: float = 497.0

    # Follow-up delays in minutes [second follow-up, third follow-up]
    follow_up_delay_minutes: str = "1440,4320"

    # Google Calendar OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # Microsoft Outlook OAuth
    microsoft_client_id: str = ""
    microsoft_client_secret: str = ""

    model_config = {
        "env_file": str(_env_file),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
