"""Tests for product feed, detail, create, and votes."""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def client_with_user():
    import app.models  # noqa: F401
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
        with patch("app.services.otp_sender.send_email_otp", new_callable=AsyncMock):
            await ac.post(
                "/api/v1/auth/request-otp",
                json={"name": "Maker", "email": "maker@example.com"},
            )

        from sqlalchemy import select
        from app.models.otp import OTPCode

        async with session_factory() as session:
            otp = (await session.execute(select(OTPCode))).scalar_one()
            code = otp.code

        token_resp = await ac.post(
            "/api/v1/auth/verify-otp",
            json={"email": "maker@example.com", "code": code},
        )
        token = token_resp.json()["access_token"]
        yield ac, token, session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def test_create_and_get_product(client_with_user):
    ac, token, _ = client_with_user
    r = await ac.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Cool App",
            "tagline": "It is cool",
            "description": "D" * 20,
            "website_url": "https://example.com",
            "logo_url": None,
        },
    )
    assert r.status_code == 200
    slug = r.json()["slug"]
    assert "cool-app-" in slug

    d = await ac.get(f"/api/v1/products/{slug}")
    assert d.status_code == 200
    data = d.json()
    assert data["name"] == "Cool App"
    assert data["maker"]["name"] == "Maker"
    assert data["has_voted"] is False


async def test_today_feed_and_vote(client_with_user):
    ac, token, session_factory = client_with_user
    await ac.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Feed App",
            "tagline": "On the feed",
            "description": "Description here",
            "website_url": "https://feed.example.com",
        },
    )
    r = await ac.get("/api/v1/products/today")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1
    assert items[0]["vote_count"] == 0

    # second user to vote
    with patch("app.services.otp_sender.send_email_otp", new_callable=AsyncMock):
        await ac.post(
            "/api/v1/auth/request-otp",
            json={"name": "Voter", "email": "voter@example.com"},
        )
    from sqlalchemy import select
    from app.models.otp import OTPCode

    async with session_factory() as session:
        otp = (
            await session.execute(
                select(OTPCode).where(OTPCode.contact == "voter@example.com")
            )
        ).scalar_one()
        code = otp.code
    tr = await ac.post(
        "/api/v1/auth/verify-otp",
        json={"email": "voter@example.com", "code": code},
    )
    voter_token = tr.json()["access_token"]

    feed = await ac.get("/api/v1/products/today")
    pid = feed.json()[0]["id"]
    vr = await ac.post(
        f"/api/v1/products/{pid}/vote",
        headers={"Authorization": f"Bearer {voter_token}"},
    )
    assert vr.status_code == 200
    assert vr.json()["vote_count"] == 1

    feed2 = await ac.get(
        "/api/v1/products/today",
        headers={"Authorization": f"Bearer {voter_token}"},
    )
    assert feed2.json()[0]["has_voted"] is True

    ur = await ac.delete(
        f"/api/v1/products/{pid}/vote",
        headers={"Authorization": f"Bearer {voter_token}"},
    )
    assert ur.status_code == 200
    assert ur.json()["vote_count"] == 0


async def test_vote_duplicate_returns_409(client_with_user):
    ac, token, _ = client_with_user
    cr = await ac.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Solo",
            "tagline": "S",
            "description": "Description",
            "website_url": "https://solo.example.com",
        },
    )
    slug = cr.json()["slug"]
    dr = await ac.get(f"/api/v1/products/{slug}")
    pid = dr.json()["id"]
    h = {"Authorization": f"Bearer {token}"}
    assert (await ac.post(f"/api/v1/products/{pid}/vote", headers=h)).status_code == 200
    r2 = await ac.post(f"/api/v1/products/{pid}/vote", headers=h)
    assert r2.status_code == 409


async def test_old_product_not_in_today(client_with_user):
    ac, token, session_factory = client_with_user
    from sqlalchemy import update
    from app.models import Product

    r = await ac.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Oldie",
            "tagline": "O",
            "description": "D",
            "website_url": "https://old.example.com",
        },
    )
    assert r.status_code == 200
    slug = r.json()["slug"]
    old = datetime.now(timezone.utc) - timedelta(days=2)
    async with session_factory() as session:
        await session.execute(
            update(Product).where(Product.slug == slug).values(created_at=old)
        )
        await session.commit()

    r2 = await ac.get("/api/v1/products/today")
    slugs = [x["slug"] for x in r2.json()]
    assert slug not in slugs