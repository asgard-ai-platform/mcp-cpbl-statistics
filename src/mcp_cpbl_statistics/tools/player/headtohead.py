"""Fetch and parse head-to-head stats from /team/fighting + /team/getfightingscore."""
import json

import httpx
from bs4 import BeautifulSoup

from mcp_cpbl_statistics.models.headtohead import HeadToHeadEntry, PlayerHeadToHead
from mcp_cpbl_statistics.models.teams import TEAM_CODES, resolve_team_code
from mcp_cpbl_statistics.scraper.fetcher import _CSRF_RE, _HEADERS

_BASE_URL = "https://cpbl.com.tw"
_FIGHTING_PATH = "/team/fighting"
_API_PATH = "/team/getfightingscore"


def _parse_entry(row: dict) -> HeadToHeadEntry:
    # When acnt is a batter, each row is a pitcher they faced.
    # When acnt is a pitcher, each row is a batter who faced them.
    # In both cases the stats are from the batter's perspective.
    opponent_name = row.get("PitcherName") or row.get("HitterName") or ""
    opponent_team = row.get("PitcherTeamName") or row.get("HitterTeamName") or ""
    return HeadToHeadEntry(
        opponent_name=opponent_name,
        opponent_team=opponent_team,
        plate_appearances=row.get("PlateAppearances") or 0,
        at_bats=row.get("HitCnt") or 0,
        hits=row.get("HittingCnt") or 0,
        doubles=row.get("TwoBaseHitCnt") or 0,
        triples=row.get("ThreeBaseHitCnt") or 0,
        home_runs=row.get("HomeRunCnt") or 0,
        rbi=row.get("RunBattedINCnt") or 0,
        walks=row.get("BasesONBallsCnt") or 0,
        strikeouts=row.get("StrikeOutCnt") or 0,
        avg=row.get("Avg") or 0.0,
        obp=row.get("Obp") or 0.0,
        slg=row.get("Slg") or 0.0,
        ops=row.get("Ops") or 0.0,
    )


async def fetch_player_headtohead(
    acnt: str,
    opponent_team: str,
    kind_code: str = "A",
    year: str = "9999",
) -> PlayerHeadToHead:
    """Fetch head-to-head stats for a player against an opponent team.

    Args:
        acnt: player account ID
        opponent_team: team name (partial match) or team code (e.g. "ACN011")
        kind_code: game type code
        year: "9999" for career totals, or a specific year like "2025"
    """
    team_code = resolve_team_code(opponent_team)
    if team_code is None:
        available = ", ".join(f"{v}({k})" for k, v in TEAM_CODES.items())
        raise ValueError(
            f"Unknown team: {opponent_team!r}. Available teams: {available}"
        )
    team_name = TEAM_CODES[team_code]

    page_url = f"{_BASE_URL}{_FIGHTING_PATH}?Acnt={acnt}"

    async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
        page_resp = await client.get(page_url)
        page_resp.raise_for_status()

        m = _CSRF_RE.search(page_resp.text)
        if not m:
            raise ValueError(f"Cannot find RequestVerificationToken in {page_url}")
        token = m.group(1)

        # detect player name
        soup = BeautifulSoup(page_resp.text, "html.parser")
        name_div = soup.find("div", class_="name")
        if name_div:
            num_span = name_div.find("span", class_="number")
            if num_span:
                num_span.extract()
            player_name = name_div.get_text(strip=True)
        else:
            player_name = ""

        post_headers = {
            "RequestVerificationToken": token,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": page_url,
        }
        resp = await client.post(
            f"{_BASE_URL}{_API_PATH}",
            data={
                "acnt": acnt,
                "kindCode": kind_code,
                "year": year,
                "fightingTeamNo": team_code,
                "fightingAcnt": "",
            },
            headers=post_headers,
        )
        resp.raise_for_status()
        rows: list[dict] = json.loads(resp.json().get("FightingScore") or "[]")

        entries = [_parse_entry(r) for r in rows]

        return PlayerHeadToHead(
            acnt=acnt,
            name=player_name,
            kind_code=kind_code,
            year=year,
            opponent_team_code=team_code,
            opponent_team_name=team_name,
            entries=entries,
        )
