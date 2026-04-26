"""Generate and verify email activation tokens."""
import secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from app.config.settings import Settings

# In-memory store for activation tokens (email -> token, expires_at)
_activation_tokens: dict[str, tuple[str, datetime]] = {}


def generate_activation_token(email: str) -> str:
    """Create a one-time activation token (valid for 24 hours)."""
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    _activation_tokens[email] = (token, expires)
    return token


def verify_activation_token(email: str, token: str) -> bool:
    """Check if token is valid and not expired."""
    if email not in _activation_tokens:
        return False
    stored_token, expires = _activation_tokens[email]
    if datetime.now(timezone.utc) > expires:
        del _activation_tokens[email]
        return False
    return stored_token == token


def consume_activation_token(email: str) -> bool:
    """Mark token as used (delete it). Returns True if it existed and was valid."""
    if email in _activation_tokens:
        _, expires = _activation_tokens[email]
        if datetime.now(timezone.utc) <= expires:
            del _activation_tokens[email]
            return True
        else:
            del _activation_tokens[email]
    return False
