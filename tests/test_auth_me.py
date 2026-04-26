"""Tests for GET /auth/me protected endpoint."""
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def authed_client():
    """Fixture that provides a client with a valid JWT already obtained."""
    from app.models.base import Base
    from app.config.database import make_engine, make_session_factory
    from app.main import create_app
    from app.api.dependencies import get_db
    from unittest.mock import AsyncMock, patch

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
        with patch("app.services.otp_sender.send_email_otp", new_callable=AsyncMock):
            await ac.post("/api/v1/auth/request-otp", json={
                "name": "Alice",
                "email": "alice@example.com",
            })

        from sqlalchemy import select
        from app.models.otp import OTPCode
        async with session_factory() as session:
            otp = (await session.execute(select(OTPCode))).scalar_one()
            code = otp.code

        token_resp = await ac.post("/api/v1/auth/verify-otp", json={
            "email": "alice@example.com",
            "code": code,
        })
        token = token_resp.json()["access_token"]
        yield ac, token

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def test_me_returns_current_user(authed_client):
    ac, token = authed_client
    resp = await ac.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data


async def test_me_without_token_returns_401(authed_client):
    ac, _ = authed_client
    resp = await ac.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_with_invalid_token_returns_401(authed_client):
    ac, _ = authed_client
    resp = await ac.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert resp.status_code == 401
