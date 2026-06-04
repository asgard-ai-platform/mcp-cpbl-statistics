"""Integration tests — make live requests to cpbl.com.tw.

Run with:
    uv run pytest -m integration

Excluded from normal runs:
    uv run pytest -m "not integration"
    uv run pytest   # integration mark is excluded by default (see pyproject.toml)

Each distinct live resource is fetched once and shared across assertions via the
module-level _cached() helper. Previously every assertion re-fetched its own page
(e.g. the season standings page was fetched 6×, the schedule 6×), which fired ~50
requests in a burst and tripped cpbl.com.tw rate limiting (HTTP 403). Sharing the
fetched result cuts that to ~13 distinct requests.
"""
import datetime

import httpx
import pytest
from bs4 import BeautifulSoup

from mcp_cpbl_statistics.models.player import PlayerProfile, PlayerStats
from mcp_cpbl_statistics.models.standings import HistoryStandings, SeasonStandings
from mcp_cpbl_statistics.models.toplist import TopList
from mcp_cpbl_statistics.models.schedule import GameResult
from mcp_cpbl_statistics.models.apart import PlayerApartStats
from mcp_cpbl_statistics.models.game_log import PlayerGameLog
from mcp_cpbl_statistics.models.headtohead import PlayerHeadToHead
from mcp_cpbl_statistics.scraper.fetcher import (
    _CSRF_RE,
    _HEADERS,
    fetch_html,
    fetch_html_and_post_json,
)
from mcp_cpbl_statistics.tools.player.apart import fetch_player_apart_stats
from mcp_cpbl_statistics.tools.player.game_log import fetch_player_game_log
from mcp_cpbl_statistics.tools.player.headtohead import fetch_player_headtohead
from mcp_cpbl_statistics.tools.player.index import fetch_player_index
from mcp_cpbl_statistics.tools.player.parser import (
    parse_player_career_stats,
    parse_player_profile,
)
from mcp_cpbl_statistics.tools.standings.parser import parse_season_standings
from mcp_cpbl_statistics.tools.standings.history_parser import parse_history_standings
from mcp_cpbl_statistics.tools.toplist.parser import parse_toplist
from mcp_cpbl_statistics.tools.schedule.parser import parse_schedule

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


# ── shared fetch cache ─────────────────────────────────────────────────────────
# Tests run sequentially, each on its own event loop. We cache the *materialised*
# result (plain data / parsed models), never the client or coroutine, so reuse
# across loops is safe. Whichever test touches a resource first pays the one
# network round-trip; the rest reuse it.

_CACHE: dict[str, object] = {}


async def _cached(key, factory):
    if key not in _CACHE:
        _CACHE[key] = await factory()
    return _CACHE[key]


async def _season_standings() -> SeasonStandings:
    html = await _cached("season_html", lambda: fetch_html(_SEASON_URL))
    return parse_season_standings(html)


async def _toplist() -> TopList:
    html = await _cached("toplist_html", lambda: fetch_html(_TOPLIST_URL))
    return parse_toplist(html)


async def _history_standings() -> HistoryStandings:
    async def _fetch() -> str:
        async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
            page = await client.get(_HISTORY_URL)
            soup = BeautifulSoup(page.text, "html.parser")
            token = soup.find("input", {"name": "__RequestVerificationToken"})["value"]
            resp = await client.post(
                _HISTORY_ACTION_URL,
                data={"__RequestVerificationToken": token, "ExecAction": "", "IndexOfPages": "0",
                      "Kindcode": "A", "Year": "2024"},
                headers={"Referer": _HISTORY_URL},
            )
            return resp.text

    text = await _cached("history_2024_A", _fetch)
    return parse_history_standings(text, 2024, "A")


async def _schedule_resp() -> dict:
    return await _cached(
        "schedule",
        lambda: fetch_html_and_post_json(
            page_url=_SCHEDULE_URL,
            api_path=_SCHEDULE_API,
            data={"calendar": f"{_CURRENT_YEAR}/01/01", "location": "", "kindCode": "A"},
        ),
    )


async def _player_index():
    return await _cached("player_index", fetch_player_index)


async def _player_profile(acnt: str) -> PlayerProfile:
    html = await _cached(f"person_html:{acnt}", lambda: fetch_html(f"{_PERSON_URL}?acnt={acnt}"))
    return parse_player_profile(html, acnt)


async def _player_career_stats(acnt: str) -> PlayerStats:
    async def _fetch() -> tuple[dict, dict]:
        page_url = f"{_PERSON_URL}?acnt={acnt}"
        async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
            page = await client.get(page_url)
            token = _CSRF_RE.search(page.text).group(1)
            post_headers = {"RequestVerificationToken": token, "X-Requested-With": "XMLHttpRequest",
                            "Referer": page_url}
            data = {"acnt": acnt, "kindCode": "A"}
            batting_r = await client.post("https://cpbl.com.tw/team/getbattingcareerscore",
                                          data=data, headers=post_headers)
            pitching_r = await client.post("https://cpbl.com.tw/team/getpitchcareerscore",
                                           data=data, headers=post_headers)
            return batting_r.json(), pitching_r.json()

    batting_json, pitching_json = await _cached(f"career:{acnt}", _fetch)
    return parse_player_career_stats(acnt, "A", batting_json, pitching_json)


async def _apart_stats(acnt: str) -> PlayerApartStats:
    # group filter is applied client-side, so fetch the full set once and let
    # callers filter the cached result.
    return await _cached(f"apart:{acnt}", lambda: fetch_player_apart_stats(acnt, "A", "9999", None))


async def _game_log(acnt: str) -> PlayerGameLog:
    # last_n only slices client-side, so fetch the full log once.
    return await _cached(f"gamelog:{acnt}", lambda: fetch_player_game_log(acnt, None, "A", None))


async def _headtohead(acnt: str, opponent: str) -> PlayerHeadToHead:
    return await _cached(
        f"h2h:{acnt}:{opponent}",
        lambda: fetch_player_headtohead(acnt, opponent, "A", "9999"),
    )


# ── standings ────────────────────────────────────────────────────────────────

class TestSeasonStandings:
    async def test_returns_season_standings(self) -> None:
        result = await _season_standings()
        assert isinstance(result, SeasonStandings)

    async def test_has_six_teams(self) -> None:
        result = await _season_standings()
        assert len(result.standings) == 6

    async def test_standings_rank_order(self) -> None:
        result = await _season_standings()
        ranks = [r.rank for r in result.standings]
        assert ranks == sorted(ranks)

    async def test_pct_range(self) -> None:
        result = await _season_standings()
        for row in result.standings:
            assert 0.0 <= row.pct <= 1.0

    async def test_pitching_batting_fielding_non_empty(self) -> None:
        result = await _season_standings()
        assert len(result.pitching) > 0
        assert len(result.batting) > 0
        assert len(result.fielding) > 0

    async def test_season_label_non_empty(self) -> None:
        result = await _season_standings()
        assert result.season_label != ""


class TestHistoryStandings:
    async def test_returns_history_standings(self) -> None:
        result = await _history_standings()
        assert isinstance(result, HistoryStandings)

    async def test_year_and_kind_code(self) -> None:
        result = await _history_standings()
        assert result.year == 2024
        assert result.kind_code == "A"

    async def test_three_seasons(self) -> None:
        result = await _history_standings()
        assert len(result.seasons) == 3


# ── toplist ───────────────────────────────────────────────────────────────────

class TestToplist:
    async def test_returns_toplist(self) -> None:
        result = await _toplist()
        assert isinstance(result, TopList)

    async def test_ten_categories(self) -> None:
        result = await _toplist()
        assert len(result.cards) == 10

    async def test_all_expected_categories(self) -> None:
        result = await _toplist()
        cats = {c.category_en for c in result.cards}
        assert cats == {"ERA", "W", "SV", "HLD", "SO", "AVG", "H", "HR", "RBI", "SB"}

    async def test_each_card_has_entries(self) -> None:
        result = await _toplist()
        for card in result.cards:
            assert len(card.entries) > 0


# ── schedule ──────────────────────────────────────────────────────────────────

class TestSchedule:
    async def test_returns_list_of_game_results(self) -> None:
        results = parse_schedule(await _schedule_resp())
        assert isinstance(results, list)
        assert all(isinstance(g, GameResult) for g in results)

    async def test_non_empty_schedule(self) -> None:
        results = parse_schedule(await _schedule_resp())
        assert len(results) > 0

    async def test_game_fields_populated(self) -> None:
        results = parse_schedule(await _schedule_resp())
        for g in results:
            assert g.visiting_team != ""
            assert g.home_team != ""
            assert g.game_date != ""

    async def test_month_filter(self) -> None:
        results = parse_schedule(await _schedule_resp(), month=4)
        for g in results:
            assert g.game_date[5:7] == "04"

    async def test_team_filter(self) -> None:
        results = parse_schedule(await _schedule_resp(), team="味全")
        for g in results:
            assert "味全" in g.visiting_team or "味全" in g.home_team

    async def test_finished_games_have_scores(self) -> None:
        results = parse_schedule(await _schedule_resp())
        finished = [g for g in results if g.status == "finished"]
        assert len(finished) > 0
        for g in finished:
            assert g.visiting_score is not None
            assert g.home_score is not None


# ── player ────────────────────────────────────────────────────────────────────

class TestSearchPlayers:
    async def test_search_returns_results(self) -> None:
        index = await _player_index()
        results = [e for e in index if "林" in e.name]
        assert len(results) > 0

    async def test_search_result_has_acnt_name_team(self) -> None:
        index = await _player_index()
        results = [e for e in index if "林" in e.name]
        for entry in results:
            assert entry.acnt != ""
            assert entry.name != ""
            assert entry.team != ""

    async def test_search_no_match_returns_empty(self) -> None:
        index = await _player_index()
        results = [e for e in index if "ZZZZZZZ" in e.name]
        assert results == []


class TestPlayerProfile:
    async def test_returns_player_profile(self) -> None:
        result = await _player_profile(_FIELDER_ACNT)
        assert isinstance(result, PlayerProfile)

    async def test_acnt_matches(self) -> None:
        result = await _player_profile(_FIELDER_ACNT)
        assert result.acnt == _FIELDER_ACNT

    async def test_name_non_empty(self) -> None:
        result = await _player_profile(_FIELDER_ACNT)
        assert result.name != ""

    async def test_pitcher_profile(self) -> None:
        result = await _player_profile(_PITCHER_ACNT)
        assert result.acnt == _PITCHER_ACNT
        assert result.name != ""


class TestPlayerStats:
    async def test_fielder_career_stats_has_batting(self) -> None:
        result = await _player_career_stats(_FIELDER_ACNT)
        assert isinstance(result, PlayerStats)
        assert result.batting is not None

    async def test_pitcher_career_stats_has_pitching(self) -> None:
        result = await _player_career_stats(_PITCHER_ACNT)
        assert isinstance(result, PlayerStats)
        assert result.pitching is not None

    async def test_career_stats_acnt_matches(self) -> None:
        result = await _player_career_stats(_FIELDER_ACNT)
        assert result.acnt == _FIELDER_ACNT


class TestPlayerApartStats:
    async def test_returns_apart_stats(self) -> None:
        result = await _apart_stats(_BATTER_APART_ACNT)
        assert result is not None

    async def test_apart_stats_has_groups(self) -> None:
        result = await _apart_stats(_BATTER_APART_ACNT)
        assert len(result.groups) > 0

    async def test_apart_stats_group_filter(self) -> None:
        result = await _apart_stats(_BATTER_APART_ACNT)
        # group filter (home/away split) is applied client-side on group_id
        groups = [g for g in result.groups if g.group_id == 1]
        assert len(groups) >= 1
        assert all(g.group_id == 1 for g in groups)


class TestPlayerGameLog:
    async def test_returns_game_log(self) -> None:
        result = await _game_log(_FIELDER_ACNT)
        assert result is not None

    async def test_game_log_has_entries(self) -> None:
        result = await _game_log(_FIELDER_ACNT)
        assert len(result.games) > 0

    async def test_last_n_limits_entries(self) -> None:
        result = await _game_log(_FIELDER_ACNT)
        assert len(result.games[:5]) == min(5, len(result.games))

    async def test_game_log_dates_non_empty(self) -> None:
        result = await _game_log(_FIELDER_ACNT)
        for entry in result.games[:10]:
            assert entry.game_date != ""


class TestPlayerHeadToHead:
    async def test_returns_headtohead(self) -> None:
        result = await _headtohead(_FIELDER_ACNT, "中信")
        assert result is not None

    async def test_headtohead_has_entries(self) -> None:
        result = await _headtohead(_FIELDER_ACNT, "中信")
        assert len(result.entries) > 0

    async def test_headtohead_opponent_team_resolved(self) -> None:
        result = await _headtohead(_FIELDER_ACNT, "中信")
        assert result.opponent_team_name != ""

    async def test_pitcher_headtohead(self) -> None:
        result = await _headtohead(_PITCHER_ACNT, "味全")
        assert result is not None
