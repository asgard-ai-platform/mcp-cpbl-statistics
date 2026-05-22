from pydantic import BaseModel


class BattingGameEntry(BaseModel):
    """打者單場成績"""
    game_date: str          # YYYY-MM-DD
    game_no: int            # 球隊本季第 N 場
    opponent: str           # 對手球隊縮寫
    plate_appearances: int
    at_bats: int
    hits: int
    doubles: int
    triples: int
    home_runs: int
    rbi: int
    runs: int
    walks: int
    strikeouts: int
    stolen_bases: int
    avg: float              # 截至該場的本季打擊率


class PitchingGameEntry(BaseModel):
    """投手單場成績"""
    game_date: str
    game_no: int
    opponent: str
    innings_pitched: float
    hits: int
    home_runs: int
    walks: int
    strikeouts: int
    runs: int
    earned_runs: int
    era: float              # 截至該場的本季防禦率
    win: bool
    loss: bool
    save: bool


class PlayerGameLog(BaseModel):
    """球員逐場成績"""
    acnt: str
    name: str
    year: str
    kind_code: str
    position: str           # "batter" 或 "pitcher"
    games: list[BattingGameEntry] | list[PitchingGameEntry]
