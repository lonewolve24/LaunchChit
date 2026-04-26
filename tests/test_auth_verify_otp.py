"""Tests for POST /auth/verify-otp endpoint."""
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def client_with_user():
    """Fixture that provides a test client with a seeded user and OTP."""
    from app.models.base import Base
    from app.models.user import User
    from app.models.otp import OTPCode
    from app.config.database import make_engine, make_session_factory
    from app.main import create_app
    from app.api.dependencies import get_db

    engine = make_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = make_session_factory(engine)

    # Seed user + valid OTP
    async with session_factory() as session:
        user = User(name="Alice", email="alice@example.com")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        valid_otp = OTPCode(
            user_id=user.id,
            code="123456",
            contact="alice@example.com",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        expired_otp = OTPCode(
            user_id=user.id,
            code="999999",
            contact="alice@example.com",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        session.add(valid_otp)
        session.add(expired_otp)
        await session.commit()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def test_verify_valid_otp_returns_jwt(client_with_user):
    resp = await client_with_user.post("/api/v1/auth/verify-otp", json={
        "email": "alice@example.com",
        "code": "123456",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_verify_wrong_code_returns_401(client_with_user):
    resp = await client_with_user.post("/api/v1/auth/verify-otp", json={
        "email": "alice@example.com",
        "code": "000000",
    })
    assert resp.status_code == 401


async def test_verify_expired_otp_returns_401(client_with_user):
    resp = await client_with_user.post("/api/v1/auth/verify-otp", json={
        "email": "alice@example.com",
        "code": "999999",
    })
    assert resp.status_code == 401


async def test_verify_otp_marks_code_as_used(client_with_user):
    await client_with_user.post("/api/v1/auth/verify-otp", json={
        "email": "alice@example.com",
        "code": "123456",
    })
    # Second attempt with same code should fail
    resp = await client_with_user.post("/api/v1/auth/verify-otp", json={
        "email": "alice@example.com",
        "code": "123456",
    })
    assert resp.status_code == 401


async def test_verify_unknown_email_returns_401(client_with_user):
    resp = await client_with_user.post("/api/v1/auth/verify-otp", json={
        "email": "nobody@example.com",
        "code": "123456",
    })
    assert resp.status_code == 401
