from pathlib import Path

import pytest

from mcp_cpbl_statistics.tools.season_standings.parser import parse_season_standings

FIXTURE = Path(__file__).parent / "fixtures" / "season_standings.html"


@pytest.fixture()
def html() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def test_season_label(html: str) -> None:
    result = parse_season_standings(html)
    assert result.season_label != ""


def test_standings_count(html: str) -> None:
    result = parse_season_standings(html)
    assert len(result.standings) == 6


def test_standings_rank_order(html: str) -> None:
    result = parse_season_standings(html)
    ranks = [r.rank for r in result.standings]
    assert ranks == sorted(ranks)


def test_standings_first_team(html: str) -> None:
    result = parse_season_standings(html)
    first = result.standings[0]
    assert first.rank == 1
    assert first.wins > 0
    assert 0.0 <= first.pct <= 1.0


def test_pitching_count(html: str) -> None:
    result = parse_season_standings(html)
    assert len(result.pitching) == 6


def test_pitching_era_positive(html: str) -> None:
    result = parse_season_standings(html)
    for row in result.pitching:
        assert row.era >= 0.0


def test_batting_count(html: str) -> None:
    result = parse_season_standings(html)
    assert len(result.batting) == 6


def test_batting_avg_range(html: str) -> None:
    result = parse_season_standings(html)
    for row in result.batting:
        assert 0.0 <= row.avg <= 1.0


def test_fielding_count(html: str) -> None:
    result = parse_season_standings(html)
    assert len(result.fielding) == 6


def test_fielding_fpct_range(html: str) -> None:
    result = parse_season_standings(html)
    for row in result.fielding:
        assert 0.0 <= row.fpct <= 1.0
