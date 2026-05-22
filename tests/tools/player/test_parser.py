import json
from pathlib import Path

import pytest

from mcp_cpbl_statistics.models.player import BattingVsEntry, PitchingVsEntry
from mcp_cpbl_statistics.tools.player.parser import (
    parse_player_career_stats,
    parse_player_profile,
    parse_player_yearly_stats,
    parse_vs_teams,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


# ──────────────────────────────────────────────
# PlayerProfile
# ──────────────────────────────────────────────

@pytest.fixture()
def html_pitcher() -> str:
    return (FIXTURES / "player_4626.html").read_text(encoding="utf-8")


@pytest.fixture()
def html_fielder() -> str:
    return (FIXTURES / "player_1339.html").read_text(encoding="utf-8")


def test_profile_pitcher_name(html_pitcher: str) -> None:
    p = parse_player_profile(html_pitcher, "0000004626")
    assert p.name == "王奕凱"
    assert p.acnt == "0000004626"


def test_profile_pitcher_number(html_pitcher: str) -> None:
    p = parse_player_profile(html_pitcher, "0000004626")
    assert p.number == "54"


def test_profile_pitcher_position(html_pitcher: str) -> None:
    p = parse_player_profile(html_pitcher, "0000004626")
    assert p.position == "投手"


def test_profile_pitcher_height_weight(html_pitcher: str) -> None:
    p = parse_player_profile(html_pitcher, "0000004626")
    assert p.height_cm == 186
    assert p.weight_kg == 93


def test_profile_pitcher_birthday(html_pitcher: str) -> None:
    p = parse_player_profile(html_pitcher, "0000004626")
    assert p.birthday == "2000/08/29"


def test_profile_fielder_name(html_fielder: str) -> None:
    p = parse_player_profile(html_fielder, "0000001339")
    assert p.name == "林祖傑"


def test_profile_fielder_position(html_fielder: str) -> None:
    p = parse_player_profile(html_fielder, "0000001339")
    assert p.position == "游擊手"


# ──────────────────────────────────────────────
# Career stats
# ──────────────────────────────────────────────

def test_career_pitcher_has_pitching_no_batting() -> None:
    acnt = "0000004626"
    result = parse_player_career_stats(
        acnt, "A",
        _load(f"batting_{acnt}.json"),
        _load(f"pitching_{acnt}.json"),
    )
    assert result.pitching is not None
    assert result.batting is None
    assert result.pitching.games > 0
    assert result.year is None
    assert result.pitching.year is None


def test_career_fielder_has_batting() -> None:
    acnt = "0000001339"
    result = parse_player_career_stats(
        acnt, "A",
        _load(f"batting_{acnt}.json"),
        _load(f"pitching_{acnt}.json"),
    )
    assert result.batting is not None
    assert result.batting.games > 0
    assert 0.0 <= result.batting.avg <= 1.0
    assert 0.0 <= result.batting.obp <= 1.0
    assert result.year is None
    assert result.batting.year is None


def test_career_name_extracted() -> None:
    acnt = "0000001339"
    result = parse_player_career_stats(
        acnt, "A",
        _load(f"batting_{acnt}.json"),
        _load(f"pitching_{acnt}.json"),
    )
    assert result.name == "林祖傑"


def test_career_kind_code_preserved() -> None:
    acnt = "0000001339"
    result = parse_player_career_stats(
        acnt, "A",
        _load(f"batting_{acnt}.json"),
        _load(f"pitching_{acnt}.json"),
    )
    assert result.kind_code == "A"


# ──────────────────────────────────────────────
# Yearly stats
# ──────────────────────────────────────────────

def test_yearly_pitcher_specific_year() -> None:
    acnt = "0000004626"
    result = parse_player_yearly_stats(
        acnt, "A", 2021,
        _load(f"batting_yearly_{acnt}.json"),
        _load(f"pitching_yearly_{acnt}.json"),
    )
    assert result.year == 2021
    assert result.pitching is not None
    assert result.pitching.year == 2021
    assert result.pitching.games > 0
    assert result.batting is None


def test_yearly_fielder_specific_year() -> None:
    acnt = "0000001339"
    result = parse_player_yearly_stats(
        acnt, "A", 2024,
        _load(f"batting_yearly_{acnt}.json"),
        _load(f"pitching_yearly_{acnt}.json"),
    )
    assert result.year == 2024
    assert result.batting is not None
    assert result.batting.year == 2024
    assert result.batting.games > 0
    assert 0.0 <= result.batting.avg <= 1.0


def test_yearly_not_found_raises() -> None:
    acnt = "0000001339"
    with pytest.raises(ValueError, match="No stats found"):
        parse_player_yearly_stats(
            acnt, "A", 2000,  # 不存在的年份
            _load(f"batting_yearly_{acnt}.json"),
            _load(f"pitching_yearly_{acnt}.json"),
        )


def test_yearly_vs_teams_none_when_no_fighter_resp() -> None:
    acnt = "0000001339"
    result = parse_player_yearly_stats(
        acnt, "A", 2024,
        _load(f"batting_yearly_{acnt}.json"),
        _load(f"pitching_yearly_{acnt}.json"),
        fighter_resp=None,
    )
    assert result.vs_teams is None


def test_yearly_fielder_vs_teams() -> None:
    acnt = "0000001339"
    result = parse_player_yearly_stats(
        acnt, "A", 2026,
        _load(f"batting_yearly_{acnt}.json"),
        _load(f"pitching_yearly_{acnt}.json"),
        fighter_resp=_load(f"fighter_{acnt}.json"),
    )
    assert result.vs_teams is not None
    assert len(result.vs_teams) > 0
    for entry in result.vs_teams:
        assert isinstance(entry, BattingVsEntry)
        assert entry.opponent != ""
        assert 0.0 <= entry.avg <= 1.0


def test_yearly_pitcher_vs_teams() -> None:
    acnt = "0000004626"
    result = parse_player_yearly_stats(
        acnt, "A", 2021,
        _load(f"batting_yearly_{acnt}.json"),
        _load(f"pitching_yearly_{acnt}.json"),
        fighter_resp=_load(f"fighter_{acnt}.json"),
    )
    assert result.vs_teams is not None
    assert len(result.vs_teams) > 0
    for entry in result.vs_teams:
        assert isinstance(entry, PitchingVsEntry)
        assert entry.opponent != ""
        assert entry.era >= 0.0


# ──────────────────────────────────────────────
# parse_vs_teams
# ──────────────────────────────────────────────

def test_parse_vs_teams_batter() -> None:
    acnt = "0000001339"
    entries = parse_vs_teams(_load(f"fighter_{acnt}.json"), is_pitcher=False)
    assert len(entries) == 5
    for e in entries:
        assert isinstance(e, BattingVsEntry)


def test_parse_vs_teams_pitcher() -> None:
    acnt = "0000004626"
    entries = parse_vs_teams(_load(f"fighter_{acnt}.json"), is_pitcher=True)
    assert len(entries) == 3
    for e in entries:
        assert isinstance(e, PitchingVsEntry)


def test_parse_vs_teams_empty_resp() -> None:
    entries = parse_vs_teams({"FighterScore": "[]"}, is_pitcher=False)
    assert entries == []
