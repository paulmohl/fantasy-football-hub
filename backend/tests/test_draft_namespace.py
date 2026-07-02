"""Wave 0 stub tests for DraftNamespace Socket.IO events (DR-07, DR-09).

These tests require app.sockets.draft_namespace which does not exist until plan 04-04.
They are marked xfail and become real tests when 04-04 completes.
"""
import pytest

@pytest.mark.xfail(strict=False, reason="stub: app.sockets.draft_namespace created in plan 04-04")
@pytest.mark.asyncio
async def test_pick_propagates(async_client):
    from app.sockets.draft_namespace import DraftNamespace
    assert DraftNamespace is not None

@pytest.mark.xfail(strict=False, reason="stub: app.sockets.draft_namespace created in plan 04-04")
@pytest.mark.asyncio
async def test_commissioner_pause(async_client):
    from app.sockets.draft_namespace import DraftNamespace
    assert DraftNamespace is not None

@pytest.mark.xfail(strict=False, reason="stub: app.sockets.draft_namespace created in plan 04-04")
@pytest.mark.asyncio
async def test_connect_rejects_missing_auth(async_client):
    pytest.skip("requires Socket.IO test client setup — implement in plan 04-04 wave")

@pytest.mark.xfail(strict=False, reason="stub: app.sockets.draft_namespace created in plan 04-04")
@pytest.mark.asyncio
async def test_non_commissioner_pause_rejected(async_client):
    pytest.skip("requires Socket.IO test client setup — implement in plan 04-04 wave")
