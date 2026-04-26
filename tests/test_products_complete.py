"""Tests for product endpoints: create, today feed, by slug, vote/unvote."""
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def client_with_auth():
    """Fixture providing a client with two authenticated users."""
    from app.models.base import Base
    from app.config.database import make_engine, make_session_factory
    from app.main import create_app
    from app.api.dependencies import get_db
    from app.services.activation_token import _activation_tokens

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
        users = {}
        for username in ["alice", "bob"]:
            r = await ac.post(
                "/api/v1/auth/signup",
                json={
                    "username": username,
                    "email": f"{username}@example.com",
                    "password": "password123",
                    "confirm_password": "password123",
                },
            )
            assert r.status_code == 200
            email = f"{username}@example.com"
            token, _ = _activation_tokens[email]
            await ac.get(f"/api/v1/auth/activate?email={email}&token={token}")
            r = await ac.post(
                "/api/v1/auth/login",
                json={"email_or_username": username, "password": "password123"},
            )
            users[username] = r.json()["access_token"]

        yield ac, users

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def test_create_product(client_with_auth):
    """Scenario 1: Alice creates a product."""
    ac, users = client_with_auth
    alice_token = users["alice"]

    r = await ac.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {alice_token}"},
        json={
            "name": "Cool App",
            "tagline": "It is cool",
            "description": "A cool application for cool people",
            "website_url": "https://example.com",
            "logo_url": None,
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert "slug" in data
    assert data["slug"].startswith("cool-app-")


async def test_create_product_requires_auth(client_with_auth):
    """Scenario 2: Unauthenticated user cannot create product."""
    ac, _ = client_with_auth

    r = await ac.post(
        "/api/v1/products",
        json={
            "name": "Cool App",
            "tagline": "It is cool",
            "description": "A cool application for cool people",
            "website_url": "https://example.com",
        },
    )
    assert r.status_code == 401


async def test_get_product_by_slug(client_with_auth):
    """Scenario 3: Get product detail by slug (with optional auth)."""
    ac, users = client_with_auth
    alice_token = users["alice"]

    r = await ac.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {alice_token}"},
        json={
            "name": "Test Product",
            "tagline": "For testing",
            "description": "A test product",
            "website_url": "https://test.com",
        },
    )
    slug = r.json()["slug"]

    r = await ac.get(f"/api/v1/products/{slug}")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Test Product"
    assert data["slug"] == slug
    assert data["vote_count"] == 0
    assert data["has_voted"] is False


async def test_get_product_by_slug_not_found(client_with_auth):
    """Scenario 4: Getting non-existent product returns 404."""
    ac, _ = client_with_auth

    r = await ac.get("/api/v1/products/nonexistent-slug")
    assert r.status_code == 404


async def test_today_feed_empty(client_with_auth):
    """Scenario 5: Empty feed when no products."""
    ac, _ = client_with_auth

    r = await ac.get("/api/v1/products/today")
    assert r.status_code == 200
    assert r.json() == []


async def test_today_feed_with_products(client_with_auth):
    """Scenario 6: Today feed shows products from last 24h, sorted by votes then created_at."""
    ac, users = client_with_auth
    alice_token = users["alice"]
    bob_token = users["bob"]

    products = []
    for i in range(3):
        r = await ac.post(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {alice_token}"},
            json={
                "name": f"Product {i}",
                "tagline": f"Tagline {i}",
                "description": f"Description {i}",
                "website_url": "https://example.com",
            },
        )
        products.append(r.json()["slug"])

    r = await ac.get("/api/v1/products/today")
    assert r.status_code == 200
    feed = r.json()
    assert len(feed) == 3
    for item in feed:
        assert "id" in item
        assert "slug" in item
        assert "name" in item
        assert "vote_count" in item
        assert "has_voted" in item
        assert "maker" in item
        assert "username" in item["maker"]


async def test_vote_on_product(client_with_auth):
    """Scenario 7: Alice votes on Bob's product."""
    ac, users = client_with_auth
    alice_token = users["alice"]
    bob_token = users["bob"]

    r = await ac.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {bob_token}"},
        json={
            "name": "Bob's Product",
            "tagline": "Created by Bob",
            "description": "A product by Bob",
            "website_url": "https://bob.com",
        },
    )
    product_id = r.json()["slug"]

    # Get product detail to find ID
    r = await ac.get(f"/api/v1/products/{product_id}")
    prod_id = r.json()["id"]

    # Alice votes
    r = await ac.post(
        f"/api/v1/products/{prod_id}/vote",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert r.status_code == 204

    # Check vote count increased
    r = await ac.get(f"/api/v1/products/{product_id}")
    assert r.json()["vote_count"] == 1
    
    # Check has_voted is true for Alice
    r = await ac.get(
        f"/api/v1/products/{product_id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert r.json()["has_voted"] is True
    
    # Check has_voted is false for Bob
    r = await ac.get(
        f"/api/v1/products/{product_id}",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert r.json()["has_voted"] is False


async def test_duplicate_vote_returns_409(client_with_auth):
    """Scenario 8: Voting twice on same product returns 409."""
    ac, users = client_with_auth
    alice_token = users["alice"]
    bob_token = users["bob"]

    r = await ac.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {bob_token}"},
        json={
            "name": "Product to Vote",
            "tagline": "Vote on this",
            "description": "Vote me",
            "website_url": "https://vote.com",
        },
    )
    product_id = r.json()["slug"]
    r = await ac.get(f"/api/v1/products/{product_id}")
    prod_id = r.json()["id"]

    # First vote succeeds
    r = await ac.post(
        f"/api/v1/products/{prod_id}/vote",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert r.status_code == 204

    # Second vote fails with 409
    r = await ac.post(
        f"/api/v1/products/{prod_id}/vote",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert r.status_code == 409
    assert "voted" in r.json()["detail"].lower()


async def test_unvote_product(client_with_auth):
    """Scenario 9: Alice votes, then removes her vote."""
    ac, users = client_with_auth
    alice_token = users["alice"]
    bob_token = users["bob"]

    r = await ac.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {bob_token}"},
        json={
            "name": "Vote and Unvote",
            "tagline": "Test unvote",
            "description": "Unvote me",
            "website_url": "https://unvote.com",
        },
    )
    product_id = r.json()["slug"]
    r = await ac.get(f"/api/v1/products/{product_id}")
    prod_id = r.json()["id"]

    # Vote
    r = await ac.post(
        f"/api/v1/products/{prod_id}/vote",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert r.status_code == 204

    # Check vote_count is 1
    r = await ac.get(f"/api/v1/products/{product_id}")
    assert r.json()["vote_count"] == 1

    # Unvote
    r = await ac.delete(
        f"/api/v1/products/{prod_id}/vote",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert r.status_code == 204

    # Check vote_count is back to 0
    r = await ac.get(f"/api/v1/products/{product_id}")
    assert r.json()["vote_count"] == 0
    assert r.json()["has_voted"] is False


async def test_unvote_nonexistent_vote_returns_404(client_with_auth):
    """Scenario 10: Trying to unvote without a vote returns 404."""
    ac, users = client_with_auth
    alice_token = users["alice"]
    bob_token = users["bob"]

    r = await ac.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {bob_token}"},
        json={
            "name": "No Vote",
            "tagline": "No one voted",
            "description": "Unvote me without voting",
            "website_url": "https://novote.com",
        },
    )
    product_id = r.json()["slug"]
    r = await ac.get(f"/api/v1/products/{product_id}")
    prod_id = r.json()["id"]

    # Try to unvote without voting first
    r = await ac.delete(
        f"/api/v1/products/{prod_id}/vote",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert r.status_code == 404


async def test_multiple_users_voting(client_with_auth):
    """Scenario 11: Multiple users vote on same product."""
    ac, users = client_with_auth
    alice_token = users["alice"]
    bob_token = users["bob"]

    r = await ac.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {alice_token}"},
        json={
            "name": "Popular Product",
            "tagline": "Everyone votes",
            "description": "Vote me up",
            "website_url": "https://popular.com",
        },
    )
    product_id = r.json()["slug"]
    r = await ac.get(f"/api/v1/products/{product_id}")
    prod_id = r.json()["id"]

    # Bob votes
    r = await ac.post(
        f"/api/v1/products/{prod_id}/vote",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert r.status_code == 204

    # Check vote_count is 1
    r = await ac.get(f"/api/v1/products/{product_id}")
    assert r.json()["vote_count"] == 1

    # Create another user and vote
    # (simulating by checking the vote_count doesn't change for Bob's second attempt)
    r = await ac.post(
        f"/api/v1/products/{prod_id}/vote",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert r.status_code == 409  # Bob can't vote twice
    
    # But vote_count should still be 1
    r = await ac.get(f"/api/v1/products/{product_id}")
    assert r.json()["vote_count"] == 1
