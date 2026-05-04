"""Global pytest configuration with proper environment setup and dependency injection."""
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load environment variables from .env before any app imports
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Ensure environment defaults for tests
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-min32chars!")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SMTP_HOST", "smtp.mailtrap.io")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("SMTP_USERNAME", "test")
os.environ.setdefault("SMTP_PASSWORD", "test")
os.environ.setdefault("SMTP_FROM", "test@example.com")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Ensure test environment is set up before running any tests."""
    # Verify critical env vars are set
    required_vars = ["JWT_SECRET_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {missing}")
    
    # Force reload of settings to pick up env vars
    import importlib
    import app.config.settings
    importlib.reload(app.config.settings)
    
    yield
