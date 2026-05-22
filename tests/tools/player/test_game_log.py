"""Tests for player game log parser."""
import json
from pathlib import Path

import pytest

from mcp_cpbl_statistics.models.game_log import BattingGameEntry, PitchingGameEntry
from mcp_cpbl_statistics.tools.player.game_log import (
    _parse_batting_entry,
    _parse_pitching_entry,
)

FIXTURES = Path(__file__).parent / "fixtures"

BATTER_ACNT = "0000001339"
PITCHER_ACNT = "0000004626"


def _load_rows(acnt: str) -> list[dict]:
    raw = json.loads((FIXTURES / f"follow_{acnt}.json").read_text())
    return json.loads(raw.get("FollowScore", "[]"))


# ──────────────────────────────────────────────
# Batter game log
# ──────────────────────────────────────────────

@pytest.fixture()
def batter_rows() -> list[dict]:
    return _load_rows(BATTER_ACNT)


def test_batter_row_count(batter_rows: list[dict]) -> None:
    assert len(batter_rows) > 0


def test_batter_entry_type(batter_rows: list[dict]) -> None:
    entry = _parse_batting_entry(batter_rows[0])
    assert isinstance(entry, BattingGameEntry)


def test_batter_game_date_format(batter_rows: list[dict]) -> None:
    for row in batter_rows:
        entry = _parse_batting_entry(row)
        assert len(entry.game_date) == 10
        assert entry.game_date[4] == "-" and entry.game_date[7] == "-"


def test_batter_avg_range(batter_rows: list[dict]) -> None:
    for row in batter_rows:
        entry = _parse_batting_entry(row)
        assert 0.0 <= entry.avg <= 1.0


def test_batter_opponent_not_empty(batter_rows: list[dict]) -> None:
    for row in batter_rows:
        entry = _parse_batting_entry(row)
        assert entry.opponent != ""


def test_batter_game_no_positive(batter_rows: list[dict]) -> None:
    for row in batter_rows:
        entry = _parse_batting_entry(row)
        assert entry.game_no > 0


# ──────────────────────────────────────────────
# Pitcher game log
# ──────────────────────────────────────────────

@pytest.fixture()
def pitcher_rows() -> list[dict]:
    return _load_rows(PITCHER_ACNT)


def test_pitcher_row_count(pitcher_rows: list[dict]) -> None:
    assert len(pitcher_rows) > 0


def test_pitcher_entry_type(pitcher_rows: list[dict]) -> None:
    entry = _parse_pitching_entry(pitcher_rows[0])
    assert isinstance(entry, PitchingGameEntry)


def test_pitcher_game_date_format(pitcher_rows: list[dict]) -> None:
    for row in pitcher_rows:
        entry = _parse_pitching_entry(row)
        assert len(entry.game_date) == 10


def test_pitcher_era_non_negative(pitcher_rows: list[dict]) -> None:
    for row in pitcher_rows:
        entry = _parse_pitching_entry(row)
        assert entry.era >= 0.0


def test_pitcher_innings_pitched_non_negative(pitcher_rows: list[dict]) -> None:
    for row in pitcher_rows:
        entry = _parse_pitching_entry(row)
        assert entry.innings_pitched >= 0.0


def test_pitcher_opponent_not_empty(pitcher_rows: list[dict]) -> None:
    for row in pitcher_rows:
        entry = _parse_pitching_entry(row)
        assert entry.opponent != ""
