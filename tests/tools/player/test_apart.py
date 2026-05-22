"""Tests for player split stats parser (apart)."""
import json
from pathlib import Path

import pytest

from mcp_cpbl_statistics.models.apart import BattingApartEntry, PitchingApartEntry
from mcp_cpbl_statistics.tools.player.apart import _rows_to_groups

FIXTURES = Path(__file__).parent / "fixtures"

BATTER_ACNT = "0000003563"
PITCHER_ACNT = "0000000776"


def _load_rows(acnt: str) -> list[dict]:
    raw = json.loads((FIXTURES / f"apart_{acnt}.json").read_text())
    return json.loads(raw.get("ApartScore", "[]"))


# ──────────────────────────────────────────────
# Batter
# ──────────────────────────────────────────────

@pytest.fixture()
def batter_rows() -> list[dict]:
    return _load_rows(BATTER_ACNT)


def test_batter_group_count(batter_rows: list[dict]) -> None:
    groups = _rows_to_groups(batter_rows, "batter", None)
    assert len(groups) == 9


def test_batter_group_ids(batter_rows: list[dict]) -> None:
    groups = _rows_to_groups(batter_rows, "batter", None)
    ids = {g.group_id for g in groups}
    assert ids == {1, 3, 4, 5, 6, 7, 8, 9, 10}


def test_batter_entries_are_batting_type(batter_rows: list[dict]) -> None:
    groups = _rows_to_groups(batter_rows, "batter", None)
    for g in groups:
        for entry in g.entries:
            assert isinstance(entry, BattingApartEntry)


def test_batter_home_away_group(batter_rows: list[dict]) -> None:
    groups = _rows_to_groups(batter_rows, "batter", None)
    g1 = next(g for g in groups if g.group_id == 1)
    names = [e.item_name for e in g1.entries]
    assert "主場" in names
    assert "客場" in names


def test_batter_avg_range(batter_rows: list[dict]) -> None:
    groups = _rows_to_groups(batter_rows, "batter", None)
    for g in groups:
        for e in g.entries:
            assert 0.0 <= e.avg <= 1.0
            assert 0.0 <= e.obp <= 1.0
            assert 0.0 <= e.slg <= 1.0


def test_batter_group_filter(batter_rows: list[dict]) -> None:
    groups = _rows_to_groups(batter_rows, "batter", group_filter=8)
    assert len(groups) == 1
    assert groups[0].group_id == 8
    names = [e.item_name for e in groups[0].entries]
    assert any("月" in n for n in names)


def test_batter_group_filter_no_match(batter_rows: list[dict]) -> None:
    groups = _rows_to_groups(batter_rows, "batter", group_filter=99)
    assert groups == []


# ──────────────────────────────────────────────
# Pitcher
# ──────────────────────────────────────────────

@pytest.fixture()
def pitcher_rows() -> list[dict]:
    return _load_rows(PITCHER_ACNT)


def test_pitcher_group_count(pitcher_rows: list[dict]) -> None:
    groups = _rows_to_groups(pitcher_rows, "pitcher", None)
    assert len(groups) == 9


def test_pitcher_entries_are_pitching_type(pitcher_rows: list[dict]) -> None:
    groups = _rows_to_groups(pitcher_rows, "pitcher", None)
    for g in groups:
        for entry in g.entries:
            assert isinstance(entry, PitchingApartEntry)


def test_pitcher_era_non_negative(pitcher_rows: list[dict]) -> None:
    groups = _rows_to_groups(pitcher_rows, "pitcher", None)
    for g in groups:
        for e in g.entries:
            assert e.era >= 0.0


def test_pitcher_home_away_group(pitcher_rows: list[dict]) -> None:
    groups = _rows_to_groups(pitcher_rows, "pitcher", None)
    g1 = next(g for g in groups if g.group_id == 1)
    names = [e.item_name for e in g1.entries]
    assert "主場" in names
    assert "客場" in names
