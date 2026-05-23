from pydantic import BaseModel


class HeadToHeadEntry(BaseModel):
    """打者對單一投手（或投手對單一打者）的累計對決成績"""
    opponent_name: str      # 對手球員姓名
    opponent_team: str      # 對手球隊名稱
    plate_appearances: int
    at_bats: int
    hits: int
    doubles: int
    triples: int
    home_runs: int
    rbi: int
    walks: int
    strikeouts: int
    avg: float
    obp: float
    slg: float
    ops: float


class PlayerHeadToHead(BaseModel):
    """球員投打對決成績"""
    acnt: str
    name: str
    kind_code: str
    year: str               # "9999"=生涯累計 或具體年份
    opponent_team_code: str
    opponent_team_name: str
    entries: list[HeadToHeadEntry]
