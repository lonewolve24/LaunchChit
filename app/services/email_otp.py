from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
from app.config.settings import Settings
from functools import lru_cache


@lru_cache
def get_settings() -> Settings:
    return Settings()


async def send_email_otp(to_email: str, code: str) -> None:
    s = get_settings()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your LaunchChit verification code"
    msg["From"] = s.smtp_from
    msg["To"] = to_email

    body = f"Your one-time verification code is: {code}\n\nThis code expires in 10 minutes."
    msg.attach(MIMEText(body, "plain"))

    async with aiosmtplib.SMTP(hostname=s.smtp_host, port=s.smtp_port, start_tls=True) as smtp:
        await smtp.login(s.smtp_username, s.smtp_password)
        await smtp.sendmail(s.smtp_from, to_email, msg.as_string())
