"""Tests for AUTH-04 (/users/me has_leagues flag)."""
import pytest


@pytest.mark.asyncio
async def test_me_no_leagues(async_client, mocker):
    """AUTH-04: New user /users/me returns has_leagues=False."""
    # Register + verify a user, then call /users/me
    # Implementation deferred until auth endpoints exist (Wave 2)
    pytest.skip("Requires auth endpoints from Wave 2 Plan D")
