from typing import Annotated, AsyncGenerator
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

# auto_error=False so we return 401 with a clear body instead of HTTPBearer's default
http_bearer = HTTPBearer(auto_error=False)


@lru_cache
def _get_session_factory():
    from app.config.database import make_engine, make_session_factory
    from app.config.settings import Settings
    settings = Settings()
    engine = make_engine(settings.database_url)
    return make_session_factory(engine)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session_factory = _get_session_factory()
    async with session_factory() as session:
        yield session


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
    db: AsyncSession = Depends(get_db),
):
    from app.core.security import decode_access_token
    from app.models.user import User

    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = (credentials.credentials or "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
    db: AsyncSession = Depends(get_db),
):
    """Optional auth: returns user if token provided and valid, else None."""
    from app.core.security import decode_access_token
    from app.models.user import User

    if credentials is None:
        return None
    token = (credentials.credentials or "").strip()
    if not token:
        return None
    user_id = decode_access_token(token)
    if user_id is None:
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
