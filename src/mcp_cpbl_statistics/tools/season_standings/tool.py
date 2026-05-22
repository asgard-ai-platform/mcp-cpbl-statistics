from fastmcp import FastMCP

from mcp_cpbl_statistics.models.standings import SeasonStandings
from mcp_cpbl_statistics.scraper.fetcher import fetch_html
from mcp_cpbl_statistics.tools.season_standings.parser import parse_season_standings

_URL = "https://cpbl.com.tw/standings/season"


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_season_standings() -> SeasonStandings:
        """取得 CPBL 本季球隊戰績，包含勝負戰績、團隊投球、打擊、守備成績。"""
        html = await fetch_html(_URL)
        return parse_season_standings(html)
