"""Integify access token manager — login, in-memory cache, refresh."""
import asyncio
import httpx
from functools import lru_cache
from app.config.settings import Settings

# In-memory token cache. Cleared on process restart (fine for prototype).
_token_cache: dict = {}
_lock = asyncio.Lock()


@lru_cache
def get_settings() -> Settings:
    return Settings()


async def get_access_token() -> str:
    """Return a valid access token, logging in if not cached."""
    async with _lock:
        if _token_cache.get("access_token"):
            return _token_cache["access_token"]
        return await _login()


async def refresh_access_token() -> str:
    """Exchange the stored refresh token for a new access token."""
    async with _lock:
        return await _refresh()


async def _login() -> str:
    s = get_settings()
    url = f"{s.sms_api_base_url}/api/v1/auth/login"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"email": s.sms_email, "password": s.sms_password})
        resp.raise_for_status()
        data = resp.json()
    _token_cache["access_token"] = data["accessToken"]
    _token_cache["refresh_token"] = data["refreshToken"]
    return data["accessToken"]


async def _refresh() -> str:
    s = get_settings()
    url = f"{s.sms_api_base_url}/api/v1/auth/refresh"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"refreshToken": _token_cache.get("refresh_token")})
        resp.raise_for_status()
        data = resp.json()
    _token_cache["access_token"] = data["accessToken"]
    _token_cache["refresh_token"] = data["refreshToken"]
    return data["accessToken"]
