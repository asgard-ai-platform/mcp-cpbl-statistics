from typing import Literal

from pydantic import BaseModel


class GameResult(BaseModel):
    """一場比賽的資料（已結束或未來賽程）"""
    game_no: int                    # 場次編號
    game_date: str                  # YYYY-MM-DD
    game_time: str                  # HH:MM，未來賽程為預定開賽時間
    kind_code: str                  # 賽制代碼，例如 A=一軍例行賽
    visiting_team: str
    home_team: str
    field: str                      # 球場縮寫，例如「大巨蛋」

    status: Literal["finished", "scheduled", "cancelled"]

    # 以下欄位只有 status="finished" 才有值
    visiting_score: int | None = None
    home_score: int | None = None
    winning_pitcher: str = ""
    losing_pitcher: str = ""
    closer: str = ""
    mvp: str = ""
