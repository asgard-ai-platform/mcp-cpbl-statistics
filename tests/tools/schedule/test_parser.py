import json
from pathlib import Path

import pytest

from mcp_cpbl_statistics.tools.schedule.parser import parse_schedule

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def api_resp() -> dict:
    return json.loads((FIXTURES / "schedule_2026_A.json").read_text())


def test_total_game_count(api_resp: dict) -> None:
    games = parse_schedule(api_resp)
    assert len(games) == 364


def test_finished_games_have_scores(api_resp: dict) -> None:
    games = parse_schedule(api_resp)
    finished = [g for g in games if g.status == "finished"]
    assert len(finished) > 0
    for g in finished:
        assert g.visiting_score is not None
        assert g.home_score is not None


def test_scheduled_games_have_no_scores(api_resp: dict) -> None:
    games = parse_schedule(api_resp)
    scheduled = [g for g in games if g.status == "scheduled"]
    assert len(scheduled) > 0
    for g in scheduled:
        assert g.visiting_score is None
        assert g.home_score is None
        assert g.winning_pitcher == ""


def test_filter_by_month(api_resp: dict) -> None:
    games = parse_schedule(api_resp, month=3)
    assert len(games) > 0
    for g in games:
        assert g.game_date[5:7] == "03"


def test_filter_by_team(api_resp: dict) -> None:
    games = parse_schedule(api_resp, team="味全")
    assert len(games) > 0
    for g in games:
        assert "味全" in g.visiting_team or "味全" in g.home_team


def test_filter_month_and_team(api_resp: dict) -> None:
    games = parse_schedule(api_resp, month=4, team="統一")
    for g in games:
        assert g.game_date[5:7] == "04"
        assert "統一" in g.visiting_team or "統一" in g.home_team


def test_game_date_format(api_resp: dict) -> None:
    games = parse_schedule(api_resp)
    for g in games[:10]:
        assert len(g.game_date) == 10
        assert g.game_date[4] == "-" and g.game_date[7] == "-"


def test_game_time_format(api_resp: dict) -> None:
    games = parse_schedule(api_resp)
    for g in games[:10]:
        assert len(g.game_time) == 5
        assert g.game_time[2] == ":"


def test_no_match_returns_empty(api_resp: dict) -> None:
    games = parse_schedule(api_resp, team="不存在的球隊")
    assert games == []
