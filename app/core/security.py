from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from functools import lru_cache
from app.config.settings import Settings


@lru_cache
def _settings() -> Settings:
    return Settings()


def create_access_token(user_id: int) -> str:
    s = _settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=s.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, s.jwt_secret_key, algorithm=s.jwt_algorithm)


def decode_access_token(token: str) -> int | None:
    s = _settings()
    try:
        payload = jwt.decode(token, s.jwt_secret_key, algorithms=[s.jwt_algorithm])
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None
