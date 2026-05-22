"""MCP tool: get_schedule."""
import datetime
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from mcp_cpbl_statistics.models.schedule import GameResult
from mcp_cpbl_statistics.scraper.fetcher import _CSRF_RE, _HEADERS, fetch_html_and_post_json
from mcp_cpbl_statistics.tools.schedule.parser import parse_schedule

_PAGE_URL = "https://cpbl.com.tw/schedule"
_API_PATH = "/schedule/getgamedatas"

KIND_CODE_DESCRIPTIONS = (
    "A=一軍例行賽（預設）、C=一軍總冠軍賽、E=一軍季後挑戰賽、"
    "G=一軍熱身賽、B=一軍明星賽、D=二軍例行賽"
)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_schedule(
        year: Annotated[int | None, Field(description="年度，例如 2026。不填則使用當年。")] = None,
        month: Annotated[int | None, Field(description="月份（1-12）。不填則回傳全年。")] = None,
        team: Annotated[str | None, Field(description="球隊名稱（部分匹配），例如「味全」、「統一」。")] = None,
        kind_code: Annotated[str, Field(description=f"賽制代碼：{KIND_CODE_DESCRIPTIONS}")] = "A",
    ) -> list[GameResult]:
        """查詢 CPBL 賽程，可依年度、月份、球隊、賽制篩選。
        已結束的比賽包含比分、勝投/敗投/救援投手、MVP。
        未來賽程包含預定開賽時間與場地。
        """
        target_year = year or datetime.date.today().year
        api_resp = await fetch_html_and_post_json(
            page_url=_PAGE_URL,
            api_path=_API_PATH,
            data={
                "calendar": f"{target_year}/01/01",
                "location": "",
                "kindCode": kind_code,
            },
        )
        return parse_schedule(api_resp, month=month, team=team)
