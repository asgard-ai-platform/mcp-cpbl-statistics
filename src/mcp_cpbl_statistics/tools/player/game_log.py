"""Fetch and parse player game log from /team/follow + /team/getfollowscore."""
import json
import re

import httpx
from bs4 import BeautifulSoup

from mcp_cpbl_statistics.models.game_log import (
    BattingGameEntry,
    PitchingGameEntry,
    PlayerGameLog,
)
from mcp_cpbl_statistics.scraper.fetcher import _CSRF_RE, _HEADERS

_BASE_URL = "https://cpbl.com.tw"
_FOLLOW_PATH = "/team/follow"
_API_PATH = "/team/getfollowscore"


def _date(raw: str) -> str:
    """'2026-05-21T00:00:00' → '2026-05-21'"""
    return raw[:10] if raw else ""


def _parse_batting_entry(row: dict) -> BattingGameEntry:
    return BattingGameEntry(
        game_date=_date(row.get("GameDate", "")),
        game_no=row.get("TotalTeamGames") or 0,
        opponent=row.get("FightTeamAbbrName", ""),
        plate_appearances=row.get("PlateAppearances") or 0,
        at_bats=row.get("HitCnt") or 0,
        hits=row.get("HittingCnt") or 0,
        doubles=row.get("TwoBaseHitCnt") or 0,
        triples=row.get("ThreeBaseHitCnt") or 0,
        home_runs=row.get("HomeRunCnt") or 0,
        rbi=row.get("RunBattedINCnt") or 0,
        runs=row.get("ScoreCnt") or 0,
        walks=row.get("BasesONBallsCnt") or 0,
        strikeouts=row.get("StrikeOutCnt") or 0,
        stolen_bases=row.get("StealBaseOKCnt") or 0,
        avg=row.get("Avg") or 0.0,
    )


def _parse_pitching_entry(row: dict) -> PitchingGameEntry:
    ip_whole = row.get("InningPitchedCnt") or 0
    ip_thirds = row.get("InningPitchedDiv3Cnt") or 0
    innings_pitched = round(ip_whole + ip_thirds / 3, 2)
    return PitchingGameEntry(
        game_date=_date(row.get("GameDate", "")),
        game_no=row.get("TotalTeamGames") or 0,
        opponent=row.get("FightTeamAbbrName", ""),
        innings_pitched=innings_pitched,
        hits=row.get("HittingCnt") or 0,
        home_runs=row.get("HomeRunCnt") or 0,
        walks=row.get("BasesONBallsCnt") or 0,
        strikeouts=row.get("StrikeOutCnt") or 0,
        runs=row.get("RunCnt") or 0,
        earned_runs=row.get("EarnedRunCnt") or 0,
        era=row.get("Era") or 0.0,
        win=(row.get("Wins") or 0) > 0,
        loss=(row.get("Loses") or 0) > 0,
        save=(row.get("SaveOK") or 0) > 0,
    )


async def fetch_player_game_log(
    acnt: str,
    year: str | None = None,
    kind_code: str = "A",
    last_n: int | None = None,
) -> PlayerGameLog:
    """Fetch game-by-game log for a player.

    Args:
        acnt: player account ID
        year: season year string, e.g. "2026". Defaults to latest available year.
        kind_code: game type code
        last_n: if set, return only the most recent N games
    """
    page_url = f"{_BASE_URL}{_FOLLOW_PATH}?Acnt={acnt}"

    async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
        page_resp = await client.get(page_url)
        page_resp.raise_for_status()
        html = page_resp.text

        m = _CSRF_RE.search(html)
        if not m:
            raise ValueError(f"Cannot find RequestVerificationToken in {page_url}")
        token = m.group(1)

        # detect defendStation and available years from page JS
        station_match = re.search(r"defendStation:\s*['\"]([^'\"]+)['\"]", html)
        defend_station = station_match.group(1) if station_match else ""

        year_opts_match = re.search(r'yearOpts:\s*JSON\.parse\(\'(\[.*?\])\'', html)
        available_years: list[str] = []
        if year_opts_match:
            opts = json.loads(year_opts_match.group(1))
            available_years = [o["Value"] for o in opts]

        # resolve target year
        if year is None:
            target_year = available_years[0] if available_years else str(__import__('datetime').date.today().year)
        else:
            if available_years and year not in available_years:
                raise ValueError(
                    f"Year {year} not available for acnt={acnt}. "
                    f"Available: {available_years}"
                )
            target_year = year

        # detect player name
        soup = BeautifulSoup(html, "html.parser")
        name_div = soup.find("div", class_="name")
        if name_div:
            num_span = name_div.find("span", class_="number")
            if num_span:
                num_span.extract()
            player_name = name_div.get_text(strip=True)
        else:
            player_name = ""

        # fetch game log
        post_headers = {
            "RequestVerificationToken": token,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": page_url,
        }
        resp = await client.post(
            f"{_BASE_URL}{_API_PATH}",
            data={"acnt": acnt, "defendStation": defend_station, "year": target_year, "kindCode": kind_code},
            headers=post_headers,
        )
        resp.raise_for_status()
        rows: list[dict] = json.loads(resp.json().get("FollowScore") or "[]")

        # determine position from row keys
        is_pitcher = "InningPitchedCnt" in (rows[0] if rows else {})
        position = "pitcher" if is_pitcher else "batter"

        if is_pitcher:
            games = [_parse_pitching_entry(r) for r in rows]
        else:
            games = [_parse_batting_entry(r) for r in rows]

        # API returns newest-first; keep that order, then slice if last_n
        if last_n is not None:
            games = games[:last_n]

        return PlayerGameLog(
            acnt=acnt,
            name=player_name,
            year=target_year,
            kind_code=kind_code,
            position=position,
            games=games,
        )
