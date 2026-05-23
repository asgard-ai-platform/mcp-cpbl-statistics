"""Integration tests — make live requests to cpbl.com.tw.

Run with:
    uv run pytest -m integration

Excluded from normal runs:
    uv run pytest -m "not integration"
    uv run pytest   # integration mark is excluded by default (see pyproject.toml)
"""
import datetime

import pytest

from mcp_cpbl_statistics.models.player import PlayerProfile, PlayerStats
from mcp_cpbl_statistics.models.standings import HistoryStandings, SeasonStandings
from mcp_cpbl_statistics.models.toplist import TopList
from mcp_cpbl_statistics.models.schedule import GameResult
from mcp_cpbl_statistics.tools.player.apart import fetch_player_apart_stats
from mcp_cpbl_statistics.tools.player.game_log import fetch_player_game_log
from mcp_cpbl_statistics.tools.player.headtohead import fetch_player_headtohead
from mcp_cpbl_statistics.tools.player.index import fetch_player_index
from mcp_cpbl_statistics.tools.player.parser import (
    parse_player_career_stats,
    parse_player_profile,
)
from mcp_cpbl_statistics.scraper.fetcher import fetch_html, fetch_html_and_post_json, _CSRF_RE, _HEADERS
from mcp_cpbl_statistics.tools.standings.parser import parse_season_standings
from mcp_cpbl_statistics.tools.standings.history_parser import parse_history_standings
from mcp_cpbl_statistics.tools.toplist.parser import parse_toplist
from mcp_cpbl_statistics.tools.schedule.parser import parse_schedule

import httpx

pytestmark = pytest.mark.integration

# ── test fixtures ────────────────────────────────────────────────────────────

# A known active pitcher (王奕凱)
_PITCHER_ACNT = "0000004626"
# A known active fielder (林祖傑)
_FIELDER_ACNT = "0000001339"
# A known batter for apart stats
_BATTER_APART_ACNT = "0000003563"

_SEASON_URL = "https://cpbl.com.tw/standings/season"
_HISTORY_URL = "https://cpbl.com.tw/standings/history"
_HISTORY_ACTION_URL = "https://cpbl.com.tw/standings/historyaction"
_TOPLIST_URL = "https://cpbl.com.tw/stats/toplist"
_SCHEDULE_URL = "https://cpbl.com.tw/schedule"
_SCHEDULE_API = "/schedule/getgamedatas"
_PERSON_URL = "https://cpbl.com.tw/team/person"

_CURRENT_YEAR = datetime.date.today().year


# ── standings ────────────────────────────────────────────────────────────────

class TestSeasonStandings:
    async def test_returns_season_standings(self) -> None:
        html = await fetch_html(_SEASON_URL)
        result = parse_season_standings(html)
        assert isinstance(result, SeasonStandings)

    async def test_has_six_teams(self) -> None:
        html = await fetch_html(_SEASON_URL)
        result = parse_season_standings(html)
        assert len(result.standings) == 6

    async def test_standings_rank_order(self) -> None:
        html = await fetch_html(_SEASON_URL)
        result = parse_season_standings(html)
        ranks = [r.rank for r in result.standings]
        assert ranks == sorted(ranks)

    async def test_pct_range(self) -> None:
        html = await fetch_html(_SEASON_URL)
        result = parse_season_standings(html)
        for row in result.standings:
            assert 0.0 <= row.pct <= 1.0

    async def test_pitching_batting_fielding_non_empty(self) -> None:
        html = await fetch_html(_SEASON_URL)
        result = parse_season_standings(html)
        assert len(result.pitching) > 0
        assert len(result.batting) > 0
        assert len(result.fielding) > 0

    async def test_season_label_non_empty(self) -> None:
        html = await fetch_html(_SEASON_URL)
        result = parse_season_standings(html)
        assert result.season_label != ""


class TestHistoryStandings:
    async def test_returns_history_standings(self) -> None:
        async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
            page = await client.get(_HISTORY_URL)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page.text, "html.parser")
            token = soup.find("input", {"name": "__RequestVerificationToken"})["value"]
            resp = await client.post(
                _HISTORY_ACTION_URL,
                data={"__RequestVerificationToken": token, "ExecAction": "", "IndexOfPages": "0",
                      "Kindcode": "A", "Year": "2024"},
                headers={"Referer": _HISTORY_URL},
            )
        result = parse_history_standings(resp.text, 2024, "A")
        assert isinstance(result, HistoryStandings)

    async def test_year_and_kind_code(self) -> None:
        async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
            page = await client.get(_HISTORY_URL)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page.text, "html.parser")
            token = soup.find("input", {"name": "__RequestVerificationToken"})["value"]
            resp = await client.post(
                _HISTORY_ACTION_URL,
                data={"__RequestVerificationToken": token, "ExecAction": "", "IndexOfPages": "0",
                      "Kindcode": "A", "Year": "2024"},
                headers={"Referer": _HISTORY_URL},
            )
        result = parse_history_standings(resp.text, 2024, "A")
        assert result.year == 2024
        assert result.kind_code == "A"

    async def test_three_seasons(self) -> None:
        async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
            page = await client.get(_HISTORY_URL)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page.text, "html.parser")
            token = soup.find("input", {"name": "__RequestVerificationToken"})["value"]
            resp = await client.post(
                _HISTORY_ACTION_URL,
                data={"__RequestVerificationToken": token, "ExecAction": "", "IndexOfPages": "0",
                      "Kindcode": "A", "Year": "2024"},
                headers={"Referer": _HISTORY_URL},
            )
        result = parse_history_standings(resp.text, 2024, "A")
        assert len(result.seasons) == 3


# ── toplist ───────────────────────────────────────────────────────────────────

class TestToplist:
    async def test_returns_toplist(self) -> None:
        html = await fetch_html(_TOPLIST_URL)
        result = parse_toplist(html)
        assert isinstance(result, TopList)

    async def test_ten_categories(self) -> None:
        html = await fetch_html(_TOPLIST_URL)
        result = parse_toplist(html)
        assert len(result.cards) == 10

    async def test_all_expected_categories(self) -> None:
        html = await fetch_html(_TOPLIST_URL)
        result = parse_toplist(html)
        cats = {c.category_en for c in result.cards}
        assert cats == {"ERA", "W", "SV", "HLD", "SO", "AVG", "H", "HR", "RBI", "SB"}

    async def test_each_card_has_entries(self) -> None:
        html = await fetch_html(_TOPLIST_URL)
        result = parse_toplist(html)
        for card in result.cards:
            assert len(card.entries) > 0


# ── schedule ──────────────────────────────────────────────────────────────────

class TestSchedule:
    async def test_returns_list_of_game_results(self) -> None:
        api_resp = await fetch_html_and_post_json(
            page_url=_SCHEDULE_URL,
            api_path=_SCHEDULE_API,
            data={"calendar": f"{_CURRENT_YEAR}/01/01", "location": "", "kindCode": "A"},
        )
        results = parse_schedule(api_resp)
        assert isinstance(results, list)
        assert all(isinstance(g, GameResult) for g in results)

    async def test_non_empty_schedule(self) -> None:
        api_resp = await fetch_html_and_post_json(
            page_url=_SCHEDULE_URL,
            api_path=_SCHEDULE_API,
            data={"calendar": f"{_CURRENT_YEAR}/01/01", "location": "", "kindCode": "A"},
        )
        results = parse_schedule(api_resp)
        assert len(results) > 0

    async def test_game_fields_populated(self) -> None:
        api_resp = await fetch_html_and_post_json(
            page_url=_SCHEDULE_URL,
            api_path=_SCHEDULE_API,
            data={"calendar": f"{_CURRENT_YEAR}/01/01", "location": "", "kindCode": "A"},
        )
        results = parse_schedule(api_resp)
        for g in results:
            assert g.visiting_team != ""
            assert g.home_team != ""
            assert g.game_date != ""

    async def test_month_filter(self) -> None:
        api_resp = await fetch_html_and_post_json(
            page_url=_SCHEDULE_URL,
            api_path=_SCHEDULE_API,
            data={"calendar": f"{_CURRENT_YEAR}/01/01", "location": "", "kindCode": "A"},
        )
        results = parse_schedule(api_resp, month=4)
        for g in results:
            assert g.game_date[5:7] == "04"

    async def test_team_filter(self) -> None:
        api_resp = await fetch_html_and_post_json(
            page_url=_SCHEDULE_URL,
            api_path=_SCHEDULE_API,
            data={"calendar": f"{_CURRENT_YEAR}/01/01", "location": "", "kindCode": "A"},
        )
        results = parse_schedule(api_resp, team="味全")
        for g in results:
            assert "味全" in g.visiting_team or "味全" in g.home_team

    async def test_finished_games_have_scores(self) -> None:
        api_resp = await fetch_html_and_post_json(
            page_url=_SCHEDULE_URL,
            api_path=_SCHEDULE_API,
            data={"calendar": f"{_CURRENT_YEAR}/01/01", "location": "", "kindCode": "A"},
        )
        results = parse_schedule(api_resp)
        finished = [g for g in results if g.status == "finished"]
        assert len(finished) > 0
        for g in finished:
            assert g.visiting_score is not None
            assert g.home_score is not None


# ── player ────────────────────────────────────────────────────────────────────

class TestSearchPlayers:
    async def test_search_returns_results(self) -> None:
        index = await fetch_player_index()
        results = [e for e in index if "林" in e.name]
        assert len(results) > 0

    async def test_search_result_has_acnt_name_team(self) -> None:
        index = await fetch_player_index()
        results = [e for e in index if "林" in e.name]
        for entry in results:
            assert entry.acnt != ""
            assert entry.name != ""
            assert entry.team != ""

    async def test_search_no_match_returns_empty(self) -> None:
        index = await fetch_player_index()
        results = [e for e in index if "ZZZZZZZ" in e.name]
        assert results == []


class TestPlayerProfile:
    async def test_returns_player_profile(self) -> None:
        html = await fetch_html(f"{_PERSON_URL}?acnt={_FIELDER_ACNT}")
        result = parse_player_profile(html, _FIELDER_ACNT)
        assert isinstance(result, PlayerProfile)

    async def test_acnt_matches(self) -> None:
        html = await fetch_html(f"{_PERSON_URL}?acnt={_FIELDER_ACNT}")
        result = parse_player_profile(html, _FIELDER_ACNT)
        assert result.acnt == _FIELDER_ACNT

    async def test_name_non_empty(self) -> None:
        html = await fetch_html(f"{_PERSON_URL}?acnt={_FIELDER_ACNT}")
        result = parse_player_profile(html, _FIELDER_ACNT)
        assert result.name != ""

    async def test_pitcher_profile(self) -> None:
        html = await fetch_html(f"{_PERSON_URL}?acnt={_PITCHER_ACNT}")
        result = parse_player_profile(html, _PITCHER_ACNT)
        assert result.acnt == _PITCHER_ACNT
        assert result.name != ""


class TestPlayerStats:
    async def test_fielder_career_stats_has_batting(self) -> None:
        page_url = f"{_PERSON_URL}?acnt={_FIELDER_ACNT}"
        async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
            page = await client.get(page_url)
            token = _CSRF_RE.search(page.text).group(1)
            post_headers = {"RequestVerificationToken": token, "X-Requested-With": "XMLHttpRequest",
                            "Referer": page_url}
            data = {"acnt": _FIELDER_ACNT, "kindCode": "A"}
            batting_r = await client.post("https://cpbl.com.tw/team/getbattingcareerscore",
                                          data=data, headers=post_headers)
            pitching_r = await client.post("https://cpbl.com.tw/team/getpitchcareerscore",
                                           data=data, headers=post_headers)
        result = parse_player_career_stats(_FIELDER_ACNT, "A",
                                           batting_r.json(), pitching_r.json())
        assert isinstance(result, PlayerStats)
        assert result.batting is not None

    async def test_pitcher_career_stats_has_pitching(self) -> None:
        page_url = f"{_PERSON_URL}?acnt={_PITCHER_ACNT}"
        async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
            page = await client.get(page_url)
            token = _CSRF_RE.search(page.text).group(1)
            post_headers = {"RequestVerificationToken": token, "X-Requested-With": "XMLHttpRequest",
                            "Referer": page_url}
            data = {"acnt": _PITCHER_ACNT, "kindCode": "A"}
            batting_r = await client.post("https://cpbl.com.tw/team/getbattingcareerscore",
                                          data=data, headers=post_headers)
            pitching_r = await client.post("https://cpbl.com.tw/team/getpitchcareerscore",
                                           data=data, headers=post_headers)
        result = parse_player_career_stats(_PITCHER_ACNT, "A",
                                           batting_r.json(), pitching_r.json())
        assert isinstance(result, PlayerStats)
        assert result.pitching is not None

    async def test_career_stats_acnt_matches(self) -> None:
        page_url = f"{_PERSON_URL}?acnt={_FIELDER_ACNT}"
        async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
            page = await client.get(page_url)
            token = _CSRF_RE.search(page.text).group(1)
            post_headers = {"RequestVerificationToken": token, "X-Requested-With": "XMLHttpRequest",
                            "Referer": page_url}
            data = {"acnt": _FIELDER_ACNT, "kindCode": "A"}
            batting_r = await client.post("https://cpbl.com.tw/team/getbattingcareerscore",
                                          data=data, headers=post_headers)
            pitching_r = await client.post("https://cpbl.com.tw/team/getpitchcareerscore",
                                           data=data, headers=post_headers)
        result = parse_player_career_stats(_FIELDER_ACNT, "A",
                                           batting_r.json(), pitching_r.json())
        assert result.acnt == _FIELDER_ACNT


class TestPlayerApartStats:
    async def test_returns_apart_stats(self) -> None:
        result = await fetch_player_apart_stats(_BATTER_APART_ACNT, "A", "9999", None)
        assert result is not None

    async def test_apart_stats_has_groups(self) -> None:
        result = await fetch_player_apart_stats(_BATTER_APART_ACNT, "A", "9999", None)
        assert len(result.groups) > 0

    async def test_apart_stats_group_filter(self) -> None:
        result = await fetch_player_apart_stats(_BATTER_APART_ACNT, "A", "9999", 1)
        # All returned groups should have group_id == 1 (home/away split)
        assert len(result.groups) >= 1
        assert all(g.group_id == 1 for g in result.groups)


class TestPlayerGameLog:
    async def test_returns_game_log(self) -> None:
        result = await fetch_player_game_log(_FIELDER_ACNT, None, "A", None)
        assert result is not None

    async def test_game_log_has_entries(self) -> None:
        result = await fetch_player_game_log(_FIELDER_ACNT, None, "A", None)
        assert len(result.games) > 0

    async def test_last_n_limits_entries(self) -> None:
        result = await fetch_player_game_log(_FIELDER_ACNT, None, "A", last_n=5)
        assert len(result.games) <= 5

    async def test_game_log_dates_non_empty(self) -> None:
        result = await fetch_player_game_log(_FIELDER_ACNT, None, "A", last_n=10)
        for entry in result.games:
            assert entry.game_date != ""


class TestPlayerHeadToHead:
    async def test_returns_headtohead(self) -> None:
        result = await fetch_player_headtohead(_FIELDER_ACNT, "中信", "A", "9999")
        assert result is not None

    async def test_headtohead_has_entries(self) -> None:
        result = await fetch_player_headtohead(_FIELDER_ACNT, "中信", "A", "9999")
        assert len(result.entries) > 0

    async def test_headtohead_opponent_team_resolved(self) -> None:
        result = await fetch_player_headtohead(_FIELDER_ACNT, "中信", "A", "9999")
        assert result.opponent_team_name != ""

    async def test_pitcher_headtohead(self) -> None:
        result = await fetch_player_headtohead(_PITCHER_ACNT, "味全", "A", "9999")
        assert result is not None
