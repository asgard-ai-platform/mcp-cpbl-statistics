from pathlib import Path

import pytest

from mcp_cpbl_statistics.tools.standings.history_parser import parse_history_standings

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def html_2024() -> str:
    return (FIXTURES / "history_2024_A.html").read_text(encoding="utf-8")


@pytest.fixture()
def html_1990() -> str:
    return (FIXTURES / "history_1990_A.html").read_text(encoding="utf-8")


# ──────────────────────────────────────────────
# 2024 year
# ──────────────────────────────────────────────

def test_2024_year_and_kind_code(html_2024: str) -> None:
    result = parse_history_standings(html_2024, 2024, "A")
    assert result.year == 2024
    assert result.kind_code == "A"


def test_2024_three_seasons(html_2024: str) -> None:
    result = parse_history_standings(html_2024, 2024, "A")
    assert len(result.seasons) == 3


def test_2024_season_labels(html_2024: str) -> None:
    result = parse_history_standings(html_2024, 2024, "A")
    labels = [s.label for s in result.seasons]
    assert "上半季戰績" in labels
    assert "下半季戰績" in labels
    assert "全年戰績" in labels


def test_2024_standings_count(html_2024: str) -> None:
    result = parse_history_standings(html_2024, 2024, "A")
    for season in result.seasons:
        assert len(season.standings) == 6


def test_2024_rank_order(html_2024: str) -> None:
    result = parse_history_standings(html_2024, 2024, "A")
    for season in result.seasons:
        ranks = [r.rank for r in season.standings]
        assert ranks == sorted(ranks)


def test_2024_pct_range(html_2024: str) -> None:
    result = parse_history_standings(html_2024, 2024, "A")
    for season in result.seasons:
        for row in season.standings:
            assert 0.0 <= row.pct <= 1.0


# ──────────────────────────────────────────────
# 1990 year (earliest season)
# ──────────────────────────────────────────────

def test_1990_three_seasons(html_1990: str) -> None:
    result = parse_history_standings(html_1990, 1990, "A")
    assert len(result.seasons) == 3


def test_1990_has_standings(html_1990: str) -> None:
    result = parse_history_standings(html_1990, 1990, "A")
    for season in result.seasons:
        assert len(season.standings) > 0


def test_1990_first_team_rank_one(html_1990: str) -> None:
    result = parse_history_standings(html_1990, 1990, "A")
    for season in result.seasons:
        assert season.standings[0].rank == 1
