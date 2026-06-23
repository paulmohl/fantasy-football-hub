"""Tests for AUTH-02 (Google OAuth)."""
import pytest


@pytest.mark.asyncio
async def test_google_redirect(async_client):
    """AUTH-02: GET /auth/google redirects to Google accounts."""
    response = await async_client.get("/api/v1/auth/google", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert "accounts.google.com" in response.headers.get("location", "")
