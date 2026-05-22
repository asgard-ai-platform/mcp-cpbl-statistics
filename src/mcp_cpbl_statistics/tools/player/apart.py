"""Fetch and parse player split stats from /team/apart + /team/getapartscore."""
import json
import re

import httpx
from bs4 import BeautifulSoup

from mcp_cpbl_statistics.models.apart import (
    APART_GROUP_NAMES,
    ApartGroup,
    BattingApartEntry,
    PitchingApartEntry,
    PlayerApartStats,
)
from mcp_cpbl_statistics.scraper.fetcher import _CSRF_RE, _HEADERS

_BASE_URL = "https://cpbl.com.tw"
_APART_PATH = "/team/apart"
_API_PATH = "/team/getapartscore"


def _parse_batting_entry(row: dict) -> BattingApartEntry:
    return BattingApartEntry(
        item_name=row.get("ItemName", ""),
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


def _parse_pitching_entry(row: dict) -> PitchingApartEntry:
    ip_whole = row.get("InningPitchedCnt") or 0
    ip_thirds = row.get("InningPitchedDiv3Cnt") or 0
    innings_pitched = round(ip_whole + ip_thirds / 3, 2) if ip_whole or ip_thirds else 0.0
    return PitchingApartEntry(
        item_name=row.get("ItemName", ""),
        games=row.get("SPCnt") or row.get("GameResultWCnt", 0) + row.get("GameResultLCnt", 0),
        wins=row.get("GameResultWCnt") or 0,
        losses=row.get("GameResultLCnt") or 0,
        saves=row.get("SaveOKCnt") or 0,
        innings_pitched=innings_pitched,
        hits=row.get("HittingCnt") or 0,
        home_runs=row.get("HomeRunCnt") or 0,
        walks=row.get("BasesONBallsCnt") or 0,
        strikeouts=row.get("StrikeOutCnt") or 0,
        earned_runs=row.get("EarnedRunCnt") or 0,
        era=row.get("Era") or 0.0,
        whip=row.get("Whip") or 0.0,
        avg=row.get("Avg") or 0.0,
    )


def _rows_to_groups(
    rows: list[dict],
    position: str,
    group_filter: int | None,
) -> list[ApartGroup]:
    """Group raw API rows by ItemGroupCode and build ApartGroup list."""
    # collect rows per group, preserving order
    grouped: dict[int, list[dict]] = {}
    for row in rows:
        gid = row.get("ItemGroupCode") or 0
        grouped.setdefault(gid, []).append(row)

    result: list[ApartGroup] = []
    for gid, group_rows in grouped.items():
        if group_filter is not None and gid != group_filter:
            continue
        name = APART_GROUP_NAMES.get(gid, f"Group {gid}")
        if position == "batter":
            entries = [_parse_batting_entry(r) for r in group_rows]
        else:
            entries = [_parse_pitching_entry(r) for r in group_rows]
        result.append(ApartGroup(group_id=gid, group_name=name, entries=entries))

    return result


async def fetch_player_apart_stats(
    acnt: str,
    kind_code: str = "A",
    year: str = "9999",
    group: int | None = None,
) -> PlayerApartStats:
    """Fetch split stats for a player. Auto-detects position (batter/pitcher).

    If a player has both position options (兩棲), pitcher stats take priority
    since the page defaults to position=02.
    """
    page_url = f"{_BASE_URL}{_APART_PATH}?Acnt={acnt}"

    async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
        # Step 1: load page for cookie + CSRF token + position detection
        page_resp = await client.get(page_url)
        page_resp.raise_for_status()
        html = page_resp.text

        m = _CSRF_RE.search(html)
        if not m:
            raise ValueError(f"Cannot find RequestVerificationToken in {page_url}")
        token = m.group(1)

        # Step 2: detect available positions from positionOpts in page JS
        # e.g. [{"Text":"投球成績","Value":"02"}] or [{"Text":"打擊成績","Value":"01"}]
        pos_match = re.search(r'positionOpts:\s*(\[[^\]]+\])', html)
        position_opts: list[dict] = json.loads(pos_match.group(1)) if pos_match else []
        position_values = [p["Value"] for p in position_opts]

        # detect player name from page
        soup = BeautifulSoup(html, "html.parser")
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

        # Step 3: fetch stats for each detected position
        all_groups: list[ApartGroup] = []
        # position precedence: if both exist, fetch both; label by position
        for pos_value in position_values:
            resp = await client.post(
                f"{_BASE_URL}{_API_PATH}",
                data={"acnt": acnt, "kindCode": kind_code, "position": pos_value, "year": year},
                headers=post_headers,
            )
            resp.raise_for_status()
            rows: list[dict] = json.loads(resp.json().get("ApartScore") or "[]")
            position_label = "pitcher" if pos_value == "02" else "batter"
            groups = _rows_to_groups(rows, position_label, group)
            all_groups.extend(groups)

        # determine primary position label for the model
        if "01" in position_values and "02" not in position_values:
            primary_position = "batter"
        elif "02" in position_values:
            primary_position = "pitcher"
        else:
            primary_position = "unknown"

        return PlayerApartStats(
            acnt=acnt,
            name=player_name,
            kind_code=kind_code,
            year=year,
            position=primary_position,
            groups=all_groups,
        )
