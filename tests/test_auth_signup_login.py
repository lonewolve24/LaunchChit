"""Tests for password-based auth (signup, login, activation)."""
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def auth_client():
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


async def test_signup_creates_inactive_user(auth_client):
    ac, _ = auth_client
    r = await ac.post(
        "/api/v1/auth/signup",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    assert r.status_code == 200


async def test_signup_rejects_duplicate_username(auth_client):
    ac, _ = auth_client
    data = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "password123",
        "confirm_password": "password123",
    }
    await ac.post("/api/v1/auth/signup", json=data)
    r = await ac.post("/api/v1/auth/signup", json={**data, "email": "alice2@example.com"})
    assert r.status_code == 409


async def test_login_inactive_user_rejected(auth_client):
    ac, _ = auth_client
    await ac.post(
        "/api/v1/auth/signup",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    r = await ac.post(
        "/api/v1/auth/login",
        json={"email_or_username": "bob", "password": "password123"},
    )
    assert r.status_code == 403
    assert "not activated" in r.json()["detail"].lower()


async def test_activate_and_login(auth_client):
    from app.services.activation_token import generate_activation_token, _activation_tokens
    
    ac, _ = auth_client
    r = await ac.post(
        "/api/v1/auth/signup",
        json={
            "username": "charlie",
            "email": "charlie@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    assert r.status_code == 200
    
    email = "charlie@example.com"
    token, _ = _activation_tokens[email]
    
    r = await ac.get(f"/api/v1/auth/activate?email={email}&token={token}")
    assert r.status_code == 200
    assert "activated" in r.json()["detail"].lower()
    
    r = await ac.post(
        "/api/v1/auth/login",
        json={"email_or_username": "charlie", "password": "password123"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


async def test_me_with_bearer_token(auth_client):
    from app.services.activation_token import _activation_tokens
    
    ac, _ = auth_client
    r = await ac.post(
        "/api/v1/auth/signup",
        json={
            "username": "diana",
            "email": "diana@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    
    email = "diana@example.com"
    token, _ = _activation_tokens[email]
    await ac.get(f"/api/v1/auth/activate?email={email}&token={token}")
    
    r = await ac.post(
        "/api/v1/auth/login",
        json={"email_or_username": "diana", "password": "password123"},
    )
    access_token = r.json()["access_token"]
    
    r = await ac.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "diana"
    assert data["email"] == "diana@example.com"
    assert data["is_active"] is True
