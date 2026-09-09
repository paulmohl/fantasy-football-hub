"""Tests for AUTH-02 (Google OAuth)."""
import pytest


@pytest.mark.asyncio
async def test_google_redirect_without_credentials(async_client):
    """AUTH-02: /auth/google returns 503 when GOOGLE_CLIENT_ID is empty (test env)."""
    response = await async_client.get("/api/v1/auth/google", follow_redirects=False)
    # In test env GOOGLE_CLIENT_ID is empty string — should return 503
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_google_callback_missing_code_returns_400(async_client):
    """AUTH-02: /auth/google/callback with no code returns 400."""
    response = await async_client.get("/api/v1/auth/google/callback", follow_redirects=False)
    assert response.status_code == 400
