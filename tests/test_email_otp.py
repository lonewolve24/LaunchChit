"""Tests for email OTP delivery via SMTP."""
from unittest.mock import AsyncMock, patch, MagicMock
import pytest


async def test_send_email_otp_sends_message_via_smtp():
    """send_email_otp should connect to SMTP and send a message containing the OTP code."""
    mock_smtp = AsyncMock()
    mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
    mock_smtp.__aexit__ = AsyncMock(return_value=False)

    with patch("aiosmtplib.SMTP", return_value=mock_smtp), \
         patch("app.services.email_otp.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            smtp_host="smtp.mailtrap.io",
            smtp_port=587,
            smtp_username="user",
            smtp_password="pass",
            smtp_from="noreply@launchchit.com",
        )
        from app.services.email_otp import send_email_otp
        await send_email_otp("bob@example.com", "482910")

    mock_smtp.login.assert_called_once_with("user", "pass")
    mock_smtp.sendmail.assert_called_once()
    call_args = mock_smtp.sendmail.call_args
    message_str = call_args[0][2] if call_args[0] else call_args[1].get("message", "")
    assert "482910" in message_str
