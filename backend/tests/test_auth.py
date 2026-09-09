"""Tests for AUTH-01 (registration + email verification) and AUTH-03 (password reset)."""
import pytest


@pytest.mark.asyncio
async def test_register_creates_unverified_user(async_client):
    """AUTH-01: POST /auth/register creates user with is_verified=False."""
    response = await async_client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "securepassword123",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data.get("is_verified") is False


@pytest.mark.asyncio
async def test_unverified_user_cannot_login(async_client):
    """AUTH-01: Unverified user cannot log in."""
    await async_client.post("/api/v1/auth/register", json={
        "email": "unverified@example.com",
        "password": "securepassword123",
    })
    response = await async_client.post("/api/v1/auth/login", json={
        "email": "unverified@example.com",
        "password": "securepassword123",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_forgot_password_sends_email(async_client):
    """AUTH-03: POST /auth/forgot-password returns 200 even if email not found (no enumeration)."""
    response = await async_client.post("/api/v1/auth/forgot-password", json={
        "email": "nobody@example.com",
    })
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(async_client):
    """AUTH-01: Duplicate email registration returns 409."""
    payload = {"email": "dup@example.com", "password": "securepassword123"}
    await async_client.post("/api/v1/auth/register", json=payload)
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_verified_user(async_client, test_db):
    """AUTH-01: Verified user can log in and receives access token."""
    from sqlalchemy import select
    from app.models.user import User

    # Register
    await async_client.post("/api/v1/auth/register", json={
        "email": "verified@example.com",
        "password": "securepassword123",
    })

    # Directly flip is_verified in the test DB
    result = await test_db.execute(select(User).where(User.email == "verified@example.com"))
    user = result.scalar_one()
    user.is_verified = True
    await test_db.commit()

    # Login
    response = await async_client.post("/api/v1/auth/login", json={
        "email": "verified@example.com",
        "password": "securepassword123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
