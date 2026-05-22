from pydantic import BaseModel


# Group 代碼對應的維度名稱（投打共用，部分名稱略有差異但意義相近）
APART_GROUP_NAMES: dict[int, str] = {
    1: "主客場",
    3: "對戰對象",
    4: "出賽角色/壘上跑者",
    5: "壘上跑者/出局數",
    6: "出局數/局數",
    7: "局數/比分情況",
    8: "比分情況/月份",
    9: "月份/球場",
    10: "球場/打序",
}


class BattingApartEntry(BaseModel):
    """打者分項成績的一筆切片"""
    item_name: str          # 例如「主場」、「VS. 左投」、「第七月」
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


class PitchingApartEntry(BaseModel):
    """投手分項成績的一筆切片"""
    item_name: str
    games: int
    wins: int
    losses: int
    saves: int
    innings_pitched: float
    hits: int
    home_runs: int
    walks: int
    strikeouts: int
    earned_runs: int
    era: float
    whip: float
    avg: float              # 被打擊率


class ApartGroup(BaseModel):
    """一個維度（例如「月份」）的所有切片"""
    group_id: int
    group_name: str
    entries: list[BattingApartEntry] | list[PitchingApartEntry]


class PlayerApartStats(BaseModel):
    """球員分項成績"""
    acnt: str
    name: str
    kind_code: str
    year: str               # "9999"=生涯累計，或具體年份如 "2025"
    position: str           # "batter" 或 "pitcher"
    groups: list[ApartGroup]
