"""MCP tools: search_players, get_player_profile, get_player_stats,
get_player_apart_stats, get_player_game_log, get_player_headtohead."""
from typing import Annotated

import httpx
from fastmcp import FastMCP
from pydantic import Field

from mcp_cpbl_statistics.models.apart import PlayerApartStats
from mcp_cpbl_statistics.models.game_log import PlayerGameLog
from mcp_cpbl_statistics.models.headtohead import PlayerHeadToHead
from mcp_cpbl_statistics.models.player import PlayerProfile, PlayerStats
from mcp_cpbl_statistics.models.teams import TEAM_CODES
from mcp_cpbl_statistics.scraper.fetcher import _CSRF_RE, _HEADERS, fetch_html
from mcp_cpbl_statistics.tools.player.apart import fetch_player_apart_stats
from mcp_cpbl_statistics.tools.player.game_log import fetch_player_game_log
from mcp_cpbl_statistics.tools.player.headtohead import fetch_player_headtohead
from mcp_cpbl_statistics.tools.player.index import fetch_player_index
from mcp_cpbl_statistics.tools.player.parser import (
    parse_player_career_stats,
    parse_player_profile,
    parse_player_yearly_stats,
)

_BASE_URL = "https://cpbl.com.tw"
_PERSON_PATH = "/team/person"

KIND_CODE_DESCRIPTIONS = (
    "A=一軍例行賽（預設）、C=一軍總冠軍賽、E=一軍季後挑戰賽、"
    "G=一軍熱身賽、B=一軍明星賽、D=二軍例行賽"
)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def search_players(
        name: Annotated[str, Field(description="球員姓名（支援部分匹配）")],
    ) -> list[dict]:
        """依姓名搜尋 CPBL 現役球員，回傳符合的球員列表（含 acnt、姓名、球隊）。
        取得 acnt 後可再呼叫 get_player_profile 或 get_player_stats。
        """
        index = await fetch_player_index()
        query = name.strip()
        return [
            {"acnt": e.acnt, "name": e.name, "team": e.team}
            for e in index
            if query in e.name
        ]

    @mcp.tool()
    async def get_player_profile(
        acnt: Annotated[str, Field(description="球員帳號 ID，例如 0000004626")],
    ) -> PlayerProfile:
        """取得 CPBL 球員基本資料（背號、位置、投打習慣、身高體重、生日、初出場、學歷、選秀）。"""
        page_url = f"{_BASE_URL}{_PERSON_PATH}?acnt={acnt}"
        html = await fetch_html(page_url)
        return parse_player_profile(html, acnt)

    @mcp.tool()
    async def get_player_stats(
        acnt: Annotated[str, Field(description="球員帳號 ID，例如 0000004626")],
        kind_code: Annotated[str, Field(description=f"賽制代碼：{KIND_CODE_DESCRIPTIONS}")] = "A",
        year: Annotated[int | None, Field(description="年度（例如 2024）。不填則回傳生涯累計。")] = None,
    ) -> PlayerStats:
        """取得 CPBL 球員成績。
        - 不指定 year：回傳生涯累計成績
        - 指定 year：回傳該年度成績
        打者回傳打擊成績，投手回傳投球成績，兩棲球員可能兩者都有。
        """
        page_url = f"{_BASE_URL}{_PERSON_PATH}?acnt={acnt}"
        batting_resp, pitching_resp, fighter_resp = await _fetch_stats(page_url, acnt, kind_code, year)

        if year is None:
            return parse_player_career_stats(acnt, kind_code, batting_resp, pitching_resp)
        else:
            return parse_player_yearly_stats(acnt, kind_code, year, batting_resp, pitching_resp, fighter_resp)


    @mcp.tool()
    async def get_player_apart_stats(
        acnt: Annotated[str, Field(description="球員帳號 ID，例如 0000003563")],
        kind_code: Annotated[str, Field(description=f"賽制代碼：{KIND_CODE_DESCRIPTIONS}")] = "A",
        year: Annotated[str, Field(description="年度：9999=生涯累計（預設），或具體年份如 2025")] = "9999",
        group: Annotated[int | None, Field(description=(
            "指定分項維度（不填則回傳全部）："
            "1=主客場、3=對戰對象、4=出賽角色/壘上跑者、5=壘上跑者/出局數、"
            "6=出局數/局數、7=局數/比分情況、8=比分情況/月份、9=月份/球場、10=球場/打序"
        ))] = None,
    ) -> PlayerApartStats:
        """取得 CPBL 球員分項成績（進階切片統計）。
        自動偵測球員為打者或投手，回傳各維度下的分項數據。
        打者欄位：PA、H、HR、RBI、AVG、OBP、SLG、OPS。
        投手欄位：G、W、L、SV、IP、H、HR、BB、K、ERA、WHIP。
        """
        return await fetch_player_apart_stats(acnt, kind_code, year, group)

    @mcp.tool()
    async def get_player_game_log(
        acnt: Annotated[str, Field(description="球員帳號 ID，例如 0000001339")],
        year: Annotated[str | None, Field(description="年度，例如 '2026'。不填則使用最新可用年份。")] = None,
        kind_code: Annotated[str, Field(description=f"賽制代碼：{KIND_CODE_DESCRIPTIONS}")] = "A",
        last_n: Annotated[int | None, Field(description="只回傳最近 N 場（例如 10）。不填則回傳全季。")] = None,
    ) -> PlayerGameLog:
        """取得 CPBL 球員逐場成績。
        打者回傳每場打擊數據（PA、H、HR、RBI、AVG 等）。
        投手回傳每場投球數據（IP、H、BB、K、ERA 等）。
        API 回傳順序為最新場次在前，適合查詢球員近況。
        """
        return await fetch_player_game_log(acnt, year, kind_code, last_n)

    _team_list = "、".join(f"{v}({k})" for k, v in TEAM_CODES.items())

    @mcp.tool()
    async def get_player_headtohead(
        acnt: Annotated[str, Field(description="球員帳號 ID，例如 0000001339")],
        opponent_team: Annotated[str, Field(description=(
            f"對手球隊名稱（支援部分匹配）或球隊代碼。可用球隊：{_team_list}"
        ))],
        kind_code: Annotated[str, Field(description=f"賽制代碼：{KIND_CODE_DESCRIPTIONS}")] = "A",
        year: Annotated[str, Field(description="年度：9999=生涯累計（預設），或具體年份如 2025")] = "9999",
    ) -> PlayerHeadToHead:
        """取得 CPBL 球員對特定球隊的投打對決成績。
        打者：回傳對該球隊每位投手的累計打擊成績（AVG/OBP/SLG/OPS/HR/RBI 等）。
        投手：回傳該球隊每位打者面對此投手的累計成績。
        支援球隊名稱部分匹配，例如「中信」、「味全」、「統一」。
        """
        return await fetch_player_headtohead(acnt, opponent_team, kind_code, year)


async def _fetch_stats(
    page_url: str,
    acnt: str,
    kind_code: str,
    year: int | None,
) -> tuple[dict, dict, dict | None]:
    """Fetch batting + pitching + (yearly only) fighter stats in one session.

    Returns (batting_resp, pitching_resp, fighter_resp).
    fighter_resp is None when year is None (career mode).
    """
    import re as _re
    from bs4 import BeautifulSoup as _BS

    if year is None:
        batting_endpoint = "/team/getbattingcareerscore"
        pitching_endpoint = "/team/getpitchcareerscore"
    else:
        batting_endpoint = "/team/getbattingscore"
        pitching_endpoint = "/team/getpitchscore"

    async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
        page_resp = await client.get(page_url)
        page_resp.raise_for_status()

        m = _CSRF_RE.search(page_resp.text)
        if not m:
            raise ValueError(f"Cannot find RequestVerificationToken in {page_url}")
        token = m.group(1)

        post_headers = {
            "RequestVerificationToken": token,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": page_url,
        }
        data = {"acnt": acnt, "kindCode": kind_code}
        origin = _BASE_URL

        batting_r = await client.post(f"{origin}{batting_endpoint}", data=data, headers=post_headers)
        pitching_r = await client.post(f"{origin}{pitching_endpoint}", data=data, headers=post_headers)
        batting_r.raise_for_status()
        pitching_r.raise_for_status()

        fighter_resp = None
        if year is not None:
            # detect defendStation from page HTML
            soup = _BS(page_resp.text, "html.parser")
            station_m = _re.search(r"defendStation:\s*['\"]([^'\"]+)['\"]", page_resp.text)
            defend_station = station_m.group(1) if station_m else ""

            fighter_r = await client.post(
                f"{origin}/team/getfighterscore",
                data={"acnt": acnt, "year": str(year), "defendStation": defend_station},
                headers=post_headers,
            )
            fighter_r.raise_for_status()
            fighter_resp = fighter_r.json()

        return batting_r.json(), pitching_r.json(), fighter_resp
