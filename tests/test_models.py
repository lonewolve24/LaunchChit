"""Tests for User and OTPCode models with SQLite async."""
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    from app.models.base import Base
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def test_create_user_with_email(db_session):
    from app.models.user import User
    user = User(name="Alice", email="alice@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    assert user.id is not None
    assert user.email == "alice@example.com"
    assert user.phone is None


async def test_create_user_with_phone(db_session):
    from app.models.user import User
    user = User(name="Bob", phone="+254700000001")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    assert user.id is not None
    assert user.phone == "+254700000001"
    assert user.email is None


async def test_create_otp_code_linked_to_user(db_session):
    from app.models.user import User
    from app.models.otp import OTPCode
    user = User(name="Carol", email="carol@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    otp = OTPCode(
        user_id=user.id,
        code="123456",
        contact="carol@example.com",
        expires_at=expires,
    )
    db_session.add(otp)
    await db_session.commit()
    await db_session.refresh(otp)

    assert otp.id is not None
    assert otp.user_id == user.id
    assert otp.used is False
