from typing import AsyncGenerator
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, Header
from sqlalchemy import select


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
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    from app.core.security import decode_access_token
    from app.models.user import User

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.removeprefix("Bearer ")
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user
