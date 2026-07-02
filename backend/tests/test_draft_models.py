"""Wave 0 stub tests for Draft DB models (DR-01, DR-02, DR-08).

These tests import from app.models.draft which does not exist until plan 04-02.
They are marked xfail and become real tests when 04-02 completes.
"""
import pytest
from uuid import uuid4

@pytest.mark.xfail(strict=False, reason="stub: app.models.draft created in plan 04-02")
def test_draft_model_has_required_fields():
    from app.models.draft import Draft
    d = Draft()
    assert hasattr(d, "id")
    assert hasattr(d, "league_id")
    assert hasattr(d, "status")
    assert hasattr(d, "pick_clock_seconds")
    assert hasattr(d, "draft_order")

@pytest.mark.xfail(strict=False, reason="stub: app.models.draft created in plan 04-02")
def test_draft_pick_unique_constraint_defined():
    from app.models.draft import DraftPick
    args = DraftPick.__table_args__
    constraint_names = [c.name for c in args if hasattr(c, "name")]
    assert any("pick_num" in str(c) or "player_id" in str(c) for c in args)

@pytest.mark.xfail(strict=False, reason="stub: app.models.draft created in plan 04-02")
def test_user_draft_ranking_model_exists():
    from app.models.draft import UserDraftRanking
    r = UserDraftRanking()
    assert hasattr(r, "rank")
    assert hasattr(r, "source")
