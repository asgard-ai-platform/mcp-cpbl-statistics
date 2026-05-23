import json
import re
from typing import Annotated

import httpx
from bs4 import BeautifulSoup
from fastmcp import FastMCP
from pydantic import Field

from mcp_cpbl_statistics.models.standings import HistoryStandings, SeasonStandings
from mcp_cpbl_statistics.scraper.fetcher import _HEADERS, fetch_html
from mcp_cpbl_statistics.tools.standings.history_parser import parse_history_standings
from mcp_cpbl_statistics.tools.standings.parser import parse_season_standings

_SEASON_URL = "https://cpbl.com.tw/standings/season"
_HISTORY_URL = "https://cpbl.com.tw/standings/history"
_HISTORY_ACTION_URL = "https://cpbl.com.tw/standings/historyaction"

KIND_CODE_DESCRIPTIONS = (
    "A=一軍例行賽（預設）、C=一軍總冠軍賽、D=二軍例行賽"
)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_season_standings() -> SeasonStandings:
        """取得 CPBL 本季球隊戰績，包含勝負戰績、團隊投球、打擊、守備成績。"""
        html = await fetch_html(_SEASON_URL)
        return parse_season_standings(html)

    @mcp.tool()
    async def get_history_standings(
        year: Annotated[int, Field(description="年度，例如 2024。可查詢範圍約 1990–前一年。")],
        kind_code: Annotated[str, Field(description=f"賽制代碼：{KIND_CODE_DESCRIPTIONS}")] = "A",
    ) -> HistoryStandings:
        """取得 CPBL 指定年度的歷年球隊戰績，包含上半季、下半季、全年三段戰績。"""
        async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
            # load page for CSRF token
            page_resp = await client.get(_HISTORY_URL)
            page_resp.raise_for_status()
            soup = BeautifulSoup(page_resp.text, "html.parser")

            token_input = soup.find("input", {"name": "__RequestVerificationToken"})
            if not token_input:
                raise ValueError("Cannot find __RequestVerificationToken on history page")
            token = token_input["value"]

            # validate year against available options
            year_opts_match = re.search(
                r'yearOpts:\s*JSON\.parse\(\'(\[.*?\])\'', page_resp.text
            )
            if year_opts_match:
                available = [int(o["Value"]) for o in json.loads(year_opts_match.group(1))]
                if year not in available:
                    raise ValueError(
                        f"Year {year} not available. Range: {min(available)}–{max(available)}"
                    )

            # fetch history HTML fragment
            resp = await client.post(
                _HISTORY_ACTION_URL,
                data={
                    "__RequestVerificationToken": token,
                    "ExecAction": "",
                    "IndexOfPages": "0",
                    "Kindcode": kind_code,
                    "Year": str(year),
                },
                headers={"Referer": _HISTORY_URL},
            )
            resp.raise_for_status()

        return parse_history_standings(resp.text, year, kind_code)
