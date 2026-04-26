"""Shared test fixtures and environment setup."""
import os

# Set required env vars before any app code is imported.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("SMTP_HOST", "smtp.mailtrap.io")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("SMTP_USERNAME", "testuser")
os.environ.setdefault("SMTP_PASSWORD", "testpass")
os.environ.setdefault("SMTP_FROM", "noreply@launchchit.com")
os.environ.setdefault("SMS_EMAIL", "sms@example.com")
os.environ.setdefault("SMS_PASSWORD", "smspass")
os.environ.setdefault("SMS_SENDER_ID", "LaunchChit")
