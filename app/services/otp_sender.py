"""Dispatch OTP delivery to the correct channel."""
from app.services.email_otp import send_email_otp
from app.services.sms_otp import send_sms_otp

__all__ = ["send_email_otp", "send_sms_otp"]
