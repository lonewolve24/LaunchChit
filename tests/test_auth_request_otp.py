"""Tests for POST /auth/request-otp endpoint."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from unittest.mock import AsyncMock, patch

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def client():
    from app.models.base import Base
    from app.config.database import make_engine, make_session_factory
    from app.main import create_app
    from app.api.dependencies import get_db

    engine = make_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = make_session_factory(engine)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac, session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def test_request_otp_with_email_creates_user_and_otp(client):
    ac, session_factory = client
    with patch("app.services.otp_sender.send_email_otp", new_callable=AsyncMock):
        resp = await ac.post("/api/v1/auth/request-otp", json={
            "name": "Alice",
            "email": "alice@example.com",
        })
    assert resp.status_code == 200
    assert resp.json()["detail"] == "OTP sent"

    from app.models.user import User
    from app.models.otp import OTPCode
    async with session_factory() as session:
        user = (await session.execute(
            select(User).where(User.email == "alice@example.com")
        )).scalar_one_or_none()
        assert user is not None
        assert user.name == "Alice"

        otp = (await session.execute(
            select(OTPCode).where(OTPCode.user_id == user.id)
        )).scalar_one_or_none()
        assert otp is not None
        assert len(otp.code) == 6
        assert otp.used is False


async def test_request_otp_with_phone_creates_user_and_otp(client):
    ac, session_factory = client
    with patch("app.services.otp_sender.send_sms_otp", new_callable=AsyncMock):
        resp = await ac.post("/api/v1/auth/request-otp", json={
            "name": "Bob",
            "phone": "+254700000001",
        })
    assert resp.status_code == 200

    from app.models.user import User
    async with session_factory() as session:
        user = (await session.execute(
            select(User).where(User.phone == "+254700000001")
        )).scalar_one_or_none()
        assert user is not None


async def test_request_otp_requires_email_or_phone(client):
    ac, _ = client
    resp = await ac.post("/api/v1/auth/request-otp", json={"name": "Nobody"})
    assert resp.status_code == 422


async def test_request_otp_existing_user_gets_new_otp(client):
    ac, session_factory = client
    with patch("app.services.otp_sender.send_email_otp", new_callable=AsyncMock):
        await ac.post("/api/v1/auth/request-otp", json={
            "name": "Alice",
            "email": "alice2@example.com",
        })
        resp = await ac.post("/api/v1/auth/request-otp", json={
            "name": "Alice",
            "email": "alice2@example.com",
        })
    assert resp.status_code == 200

    from app.models.otp import OTPCode
    from app.models.user import User
    async with session_factory() as session:
        user = (await session.execute(
            select(User).where(User.email == "alice2@example.com")
        )).scalar_one_or_none()
        otps = (await session.execute(
            select(OTPCode).where(OTPCode.user_id == user.id)
        )).scalars().all()
        assert len(otps) == 2
