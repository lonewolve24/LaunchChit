import httpx
from functools import lru_cache
from app.config.settings import Settings
from app.services.integify_token import get_access_token, refresh_access_token


@lru_cache
def get_settings() -> Settings:
    return Settings()


async def send_sms_otp(to_phone: str, code: str) -> None:
    s = get_settings()
    url = f"{s.sms_api_base_url}/api/v1/messages"
    payload = {
        "text": f"Your LaunchChit verification code is: {code}",
        "phoneNumbers": [to_phone],
        "senderId": s.sms_sender_id,
    }
    token = await get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                new_token = await refresh_access_token()
                headers = {"Authorization": f"Bearer {new_token}"}
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
            else:
                raise
