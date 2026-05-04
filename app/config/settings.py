from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_ignore_empty=True
    )

    database_url: str = "sqlite+aiosqlite:///./launchchit.db"
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days
    # When true, POST /auth/dev-token can mint a JWT without OTP (dev only — never in production). Env: DEV_SIMPLE_JWT
    dev_simple_jwt: bool = False

    smtp_host: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    smtp_from: str

    # Integify SMS — use either API key (Bearer) or login (set SMS_EMAIL + SMS_PASSWORD in .env)
    # Env: SMS_API_KEY, SMS_EMAIL, SMS_PASSWORD
    sms_api_key: str = Field(default="")
    sms_email: str = Field(default="")
    sms_password: str = Field(default="")
    sms_sender_id: str = "LaunchChit"
    sms_api_base_url: str = "https://smsapi.integify.io"


def is_sms_delivery_configured() -> bool:
    """True if Integify can send SMS: static API key and/or login credentials."""
    s = Settings()
    if (s.sms_api_key or "").strip():
        return True
    return bool((s.sms_email or "").strip() and (s.sms_password or "").strip())


