"""Tests for head-to-head parser and team code resolution."""
import json
from pathlib import Path

import pytest

from mcp_cpbl_statistics.models.headtohead import HeadToHeadEntry
from mcp_cpbl_statistics.models.teams import resolve_team_code
from mcp_cpbl_statistics.tools.player.headtohead import _parse_entry

FIXTURES = Path(__file__).parent / "fixtures"

BATTER_ACNT = "0000001339"
PITCHER_ACNT = "0000000776"


def _load_rows(acnt: str, team_code: str) -> list[dict]:
    raw = json.loads((FIXTURES / f"headtohead_{acnt}_{team_code}.json").read_text())
    return json.loads(raw.get("FightingScore") or "[]")


# ──────────────────────────────────────────────
# resolve_team_code
# ──────────────────────────────────────────────

def test_resolve_exact_code() -> None:
    assert resolve_team_code("ACN011") == "ACN011"


def test_resolve_exact_name() -> None:
    assert resolve_team_code("中信兄弟") == "ACN011"


def test_resolve_partial_name() -> None:
    assert resolve_team_code("中信") == "ACN011"
    assert resolve_team_code("味全") == "AAA011"
    assert resolve_team_code("統一") == "ADD011"
    assert resolve_team_code("富邦") == "AEO011"
    assert resolve_team_code("樂天") == "AJL011"
    assert resolve_team_code("台鋼") == "AKP011"


def test_resolve_unknown_returns_none() -> None:
    assert resolve_team_code("不存在球隊") is None
    assert resolve_team_code("") is None


# ──────────────────────────────────────────────
# Batter head-to-head (batter vs pitcher team)
# ──────────────────────────────────────────────

@pytest.fixture()
def batter_rows() -> list[dict]:
    return _load_rows(BATTER_ACNT, "ACN011")


def test_batter_entry_count(batter_rows: list[dict]) -> None:
    assert len(batter_rows) > 0


def test_batter_entry_type(batter_rows: list[dict]) -> None:
    entry = _parse_entry(batter_rows[0])
    assert isinstance(entry, HeadToHeadEntry)


def test_batter_opponent_is_pitcher(batter_rows: list[dict]) -> None:
    # When acnt is a batter, PitcherName should be populated
    for row in batter_rows[:5]:
        assert row.get("PitcherName"), "Expected PitcherName for batter h2h"


def test_batter_avg_range(batter_rows: list[dict]) -> None:
    for row in batter_rows:
        entry = _parse_entry(row)
        assert 0.0 <= entry.avg <= 1.0
        assert 0.0 <= entry.obp <= 1.0


def test_batter_opponent_name_not_empty(batter_rows: list[dict]) -> None:
    for row in batter_rows:
        entry = _parse_entry(row)
        assert entry.opponent_name != ""


# ──────────────────────────────────────────────
# Pitcher head-to-head (pitcher vs batter team)
# ──────────────────────────────────────────────

@pytest.fixture()
def pitcher_rows() -> list[dict]:
    return _load_rows(PITCHER_ACNT, "ADD011")


def test_pitcher_entry_count(pitcher_rows: list[dict]) -> None:
    assert len(pitcher_rows) > 0


def test_pitcher_opponent_is_hitter(pitcher_rows: list[dict]) -> None:
    # When acnt is a pitcher, HitterName should be populated
    for row in pitcher_rows[:5]:
        assert row.get("HitterName"), "Expected HitterName for pitcher h2h"


def test_pitcher_avg_range(pitcher_rows: list[dict]) -> None:
    for row in pitcher_rows:
        entry = _parse_entry(row)
        assert 0.0 <= entry.avg <= 1.0


def test_pitcher_opponent_name_not_empty(pitcher_rows: list[dict]) -> None:
    for row in pitcher_rows:
        entry = _parse_entry(row)
        assert entry.opponent_name != ""
