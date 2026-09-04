from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "dev"

    # ── Supabase ──────────────────────────────────────────────────────────────
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # ── JWT ───────────────────────────────────────────────────────────────────
    jwt_secret: str = "scan2pay-jwt-secret-dev-change-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 30

    # ── WinSMS (same account as PredictIQ) ───────────────────────────────────
    winsms_api_url: str = "https://api.winsms.co.za/api/rest/v1"
    winsms_api_key: str = ""

    # ── Paystack ──────────────────────────────────────────────────────────────
    paystack_secret_key: str = ""
    paystack_public_key: str = ""
    paystack_webhook_secret: str = ""
    paystack_base_url: str = "https://api.paystack.co"

    # ── AWS ───────────────────────────────────────────────────────────────────
    aws_region: str = "af-south-1"

    # ── App ───────────────────────────────────────────────────────────────────
    app_name: str = "Scan2Pay API"
    api_version: str = "v1"
    cors_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
