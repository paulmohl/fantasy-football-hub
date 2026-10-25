from datetime import date

import pytest

from app.core.config import Settings, current_nfl_season


@pytest.mark.parametrize(
    "today,expected",
    [
        (date(2026, 2, 28), 2025),
        (date(2026, 3, 1), 2026),
        (date(2026, 10, 24), 2026),
        (date(2026, 12, 31), 2026),
        (date(2027, 1, 15), 2026),
    ],
)
def test_current_nfl_season(today, expected):
    assert current_nfl_season(today) == expected


def test_env_override_wins(monkeypatch):
    monkeypatch.setenv("NFL_SEASON_YEAR", "2031")
    assert Settings().nfl_season_year == 2031


def test_default_is_derived_from_today(monkeypatch):
    monkeypatch.delenv("NFL_SEASON_YEAR", raising=False)
    assert Settings().nfl_season_year == current_nfl_season()
