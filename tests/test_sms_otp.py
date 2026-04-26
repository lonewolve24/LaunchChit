"""Tests for SMS OTP delivery via Integify API with Bearer token auth."""
from unittest.mock import AsyncMock, MagicMock, patch


async def test_send_sms_otp_sends_with_bearer_token():
    """send_sms_otp should use Authorization: Bearer <token>, not X-API-Key."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client), \
         patch("app.services.sms_otp.get_settings") as mock_settings, \
         patch("app.services.sms_otp.get_access_token", new_callable=AsyncMock, return_value="token-abc"):
        mock_settings.return_value = MagicMock(
            sms_sender_id="LaunchChit",
            sms_api_base_url="https://smsapi.integify.io",
        )
        from app.services.sms_otp import send_sms_otp
        await send_sms_otp("+220123456789", "839201")

    mock_client.post.assert_called_once()
    headers = mock_client.post.call_args[1].get("headers", {})
    assert headers.get("Authorization") == "Bearer token-abc"
    assert "X-API-Key" not in headers

    body = mock_client.post.call_args[1].get("json", {})
    assert "+220123456789" in body.get("phoneNumbers", [])
    assert "839201" in body.get("text", "")


async def test_send_sms_otp_retries_with_fresh_token_on_401():
    """On a 401, send_sms_otp should refresh the token and retry once."""
    import httpx

    unauthorized = MagicMock()
    unauthorized.status_code = 401
    unauthorized.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError(
        "401", request=MagicMock(), response=unauthorized
    ))

    success = MagicMock()
    success.status_code = 200
    success.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(side_effect=[unauthorized, success])

    with patch("httpx.AsyncClient", return_value=mock_client), \
         patch("app.services.sms_otp.get_settings") as mock_settings, \
         patch("app.services.sms_otp.get_access_token", new_callable=AsyncMock, return_value="old-token"), \
         patch("app.services.sms_otp.refresh_access_token", new_callable=AsyncMock, return_value="new-token") as mock_refresh:
        mock_settings.return_value = MagicMock(
            sms_sender_id="LaunchChit",
            sms_api_base_url="https://smsapi.integify.io",
        )
        from app.services import sms_otp
        # Force reload so patches apply cleanly
        import importlib
        importlib.reload(sms_otp)

        with patch("app.services.sms_otp.get_access_token", new_callable=AsyncMock, return_value="old-token"), \
             patch("app.services.sms_otp.refresh_access_token", new_callable=AsyncMock, return_value="new-token"):
            await sms_otp.send_sms_otp("+220123456789", "111111")

    # Two POST calls: first with old token (401), second with refreshed token
    assert mock_client.post.call_count == 2
