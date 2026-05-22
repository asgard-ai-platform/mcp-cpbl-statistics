from fastmcp import FastMCP

from mcp_cpbl_statistics.models.toplist import TopList
from mcp_cpbl_statistics.scraper.fetcher import fetch_html
from mcp_cpbl_statistics.tools.toplist.parser import parse_toplist

_URL = "https://cpbl.com.tw/stats/toplist"


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_toplist() -> TopList:
        """取得 CPBL 年度單項排行榜，包含投球（ERA/W/SV/HLD/SO）和打擊（AVG/H/HR/RBI/SB）各類 Top 5。"""
        html = await fetch_html(_URL)
        return parse_toplist(html)
