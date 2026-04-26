"""Tests for app settings."""


async def test_settings_have_required_fields():
    from app.config.settings import Settings
    s = Settings(
        database_url="sqlite+aiosqlite:///./test.db",
        jwt_secret_key="testsecret",
        smtp_host="smtp.mailtrap.io",
        smtp_port=587,
        smtp_username="user",
        smtp_password="pass",
        smtp_from="noreply@launchchit.com",
        sms_email="sms@example.com",
        sms_password="smspass",
        sms_sender_id="LaunchChit",
    )
    assert s.database_url == "sqlite+aiosqlite:///./test.db"
    assert s.jwt_secret_key == "testsecret"
    assert s.jwt_algorithm == "HS256"
    assert s.jwt_expire_minutes == 60 * 24 * 7
    assert s.sms_api_base_url == "https://smsapi.integify.io"


async def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./launchchit.db")
    monkeypatch.setenv("JWT_SECRET_KEY", "mysecret")
    monkeypatch.setenv("SMTP_HOST", "smtp.mailtrap.io")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "u")
    monkeypatch.setenv("SMTP_PASSWORD", "p")
    monkeypatch.setenv("SMTP_FROM", "no@reply.com")
    monkeypatch.setenv("SMS_EMAIL", "sms@example.com")
    monkeypatch.setenv("SMS_PASSWORD", "smspass")
    monkeypatch.setenv("SMS_SENDER_ID", "LaunchChit")

    from importlib import reload
    import app.config.settings as settings_module
    reload(settings_module)
    s = settings_module.Settings()
    assert s.jwt_secret_key == "mysecret"
    assert s.smtp_host == "smtp.mailtrap.io"
    assert s.sms_email == "sms@example.com"
