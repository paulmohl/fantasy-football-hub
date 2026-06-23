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
async def test_forgot_password_sends_email(async_client, mocker):
    """AUTH-03: POST /auth/forgot-password returns 200 even if email not found (no enumeration)."""
    response = await async_client.post("/api/v1/auth/forgot-password", json={
        "email": "nobody@example.com",
    })
    assert response.status_code == 200
