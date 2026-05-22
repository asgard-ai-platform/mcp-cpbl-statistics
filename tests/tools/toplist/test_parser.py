from pathlib import Path

import pytest

from mcp_cpbl_statistics.tools.toplist.parser import parse_toplist

FIXTURE = Path(__file__).parent / "fixtures" / "toplist.html"

EXPECTED_CATEGORIES_EN = {"ERA", "W", "SV", "HLD", "SO", "AVG", "H", "HR", "RBI", "SB"}


@pytest.fixture()
def html() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def test_season_label(html: str) -> None:
    result = parse_toplist(html)
    assert "單項排行榜" in result.season_label


def test_card_count(html: str) -> None:
    result = parse_toplist(html)
    assert len(result.cards) == 10


def test_all_categories_present(html: str) -> None:
    result = parse_toplist(html)
    en_set = {c.category_en for c in result.cards}
    assert en_set == EXPECTED_CATEGORIES_EN


def test_each_card_has_5_entries(html: str) -> None:
    result = parse_toplist(html)
    for card in result.cards:
        assert len(card.entries) == 5, f"{card.category_en} has {len(card.entries)} entries"


def test_rank_order(html: str) -> None:
    result = parse_toplist(html)
    for card in result.cards:
        ranks = [e.rank for e in card.entries]
        assert ranks == list(range(1, 6)), f"{card.category_en} ranks={ranks}"


def test_entries_have_player_and_team(html: str) -> None:
    result = parse_toplist(html)
    for card in result.cards:
        for entry in card.entries:
            assert entry.player != "", f"{card.category_en} entry {entry.rank} has no player"
            assert entry.team != "", f"{card.category_en} entry {entry.rank} has no team"


def test_entries_have_value(html: str) -> None:
    result = parse_toplist(html)
    for card in result.cards:
        for entry in card.entries:
            assert entry.value != "", f"{card.category_en} entry {entry.rank} has no value"
