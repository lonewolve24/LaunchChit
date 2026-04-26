"""Tests for Integify token manager — login, cache, and refresh."""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


async def test_get_token_calls_login_and_returns_access_token():
    """First call should POST to /auth/login and return the accessToken."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "accessToken": "access-abc",
        "refreshToken": "refresh-xyz",
        "tokenType": "bearer",
    }

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client), \
         patch("app.services.integify_token.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            sms_api_base_url="https://smsapi.integify.io",
            sms_email="user@example.com",
            sms_password="secret",
        )
        from app.services import integify_token
        integify_token._token_cache.clear()

        token = await integify_token.get_access_token()

    assert token == "access-abc"
    mock_client.post.assert_called_once()
    login_url = mock_client.post.call_args[0][0]
    assert "/api/v1/auth/login" in login_url
    body = mock_client.post.call_args[1]["json"]
    assert body["email"] == "user@example.com"
    assert body["password"] == "secret"


async def test_get_token_uses_cached_token_on_second_call():
    """Second call within token lifetime should NOT make another HTTP request."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "accessToken": "cached-token",
        "refreshToken": "refresh-xyz",
        "tokenType": "bearer",
    }

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client), \
         patch("app.services.integify_token.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            sms_api_base_url="https://smsapi.integify.io",
            sms_email="user@example.com",
            sms_password="secret",
        )
        from app.services import integify_token
        integify_token._token_cache.clear()

        t1 = await integify_token.get_access_token()
        t2 = await integify_token.get_access_token()

    assert t1 == t2 == "cached-token"
    assert mock_client.post.call_count == 1  # only one login call


async def test_refresh_token_uses_refresh_endpoint():
    """refresh_access_token should POST to /auth/refresh with refreshToken."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "accessToken": "new-access",
        "refreshToken": "new-refresh",
        "tokenType": "bearer",
    }

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client), \
         patch("app.services.integify_token.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            sms_api_base_url="https://smsapi.integify.io",
            sms_email="user@example.com",
            sms_password="secret",
        )
        from app.services import integify_token
        integify_token._token_cache["access_token"] = "old-access"
        integify_token._token_cache["refresh_token"] = "old-refresh"

        new_token = await integify_token.refresh_access_token()

    assert new_token == "new-access"
    refresh_url = mock_client.post.call_args[0][0]
    assert "/api/v1/auth/refresh" in refresh_url
    body = mock_client.post.call_args[1]["json"]
    assert body["refreshToken"] == "old-refresh"
