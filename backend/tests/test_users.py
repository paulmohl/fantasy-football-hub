"""Tests for AUTH-04 (/users/me has_leagues flag)."""
import pytest


@pytest.mark.asyncio
async def test_me_no_leagues(async_client, test_db):
    """AUTH-04: New verified user /users/me returns has_leagues=False."""
    from sqlalchemy import select
    from app.models.user import User

    # Register
    await async_client.post("/api/v1/auth/register", json={
        "email": "me_test@example.com",
        "password": "securepassword123",
    })

    # Verify the user directly in test DB
    result = await test_db.execute(select(User).where(User.email == "me_test@example.com"))
    user = result.scalar_one()
    user.is_verified = True
    await test_db.commit()

    # Login to get access token
    login_resp = await async_client.post("/api/v1/auth/login", json={
        "email": "me_test@example.com",
        "password": "securepassword123",
    })
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    # Call /users/me
    me_resp = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["email"] == "me_test@example.com"
    assert data["is_verified"] is True
    assert data["has_leagues"] is False
    assert "credential_health" in data
    assert data["credential_health"] == []


@pytest.mark.asyncio
async def test_me_with_unhealthy_credential(async_client, test_db):
    """AUTH-04: /users/me credential_health includes unhealthy platforms."""
    from sqlalchemy import select
    from app.core.security import create_access_token
    from app.models.user import User
    from app.services.credential_service import CredentialService

    await async_client.post("/api/v1/auth/register", json={
        "email": "me_unhealthy@example.com",
        "password": "securepassword123",
    })

    result = await test_db.execute(select(User).where(User.email == "me_unhealthy@example.com"))
    user = result.scalar_one()
    user.is_verified = True
    await test_db.commit()
    await test_db.refresh(user)

    cred_svc = CredentialService()
    await cred_svc.store_credential(user, "yahoo", {"access_token": "t", "refresh_token": "r"}, test_db)
    await test_db.commit()
    await cred_svc.mark_unhealthy(user.id, "yahoo", test_db)
    await test_db.commit()

    login_resp = await async_client.post("/api/v1/auth/login", json={
        "email": "me_unhealthy@example.com",
        "password": "securepassword123",
    })
    access_token = login_resp.json()["access_token"]

    me_resp = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200
    data = me_resp.json()
    unhealthy = [c for c in data["credential_health"] if not c["is_healthy"]]
    assert any(c["platform"] == "yahoo" for c in unhealthy)
