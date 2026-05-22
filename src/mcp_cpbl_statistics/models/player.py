from pydantic import BaseModel


class PlayerIndexEntry(BaseModel):
    """球員 index 的一筆資料（內部用）"""
    acnt: str
    name: str
    team: str


class PlayerProfile(BaseModel):
    """球員個人基本資料"""
    acnt: str
    name: str
    number: str
    team: str
    position: str
    batting_throwing: str   # 例如「右投右打」
    height_cm: int | None
    weight_kg: int | None
    birthday: str           # YYYY/MM/DD
    debut: str              # YYYY/MM/DD
    education: str
    nationality: str
    draft: str              # 選秀順位，可能為空


class BattingStats(BaseModel):
    """打擊生涯/年度成績"""
    year: int | None = None   # None 表示生涯累計
    games: int
    plate_appearances: int
    at_bats: int
    hits: int
    doubles: int
    triples: int
    home_runs: int
    rbi: int
    runs: int
    strikeouts: int
    walks: int
    stolen_bases: int
    avg: float
    obp: float
    slg: float
    ops: float


class PitchingStats(BaseModel):
    """投球生涯/年度成績"""
    year: int | None = None   # None 表示生涯累計
    games: int
    wins: int
    losses: int
    saves: int
    holds: int
    innings_pitched: float
    hits: int
    home_runs: int
    walks: int
    strikeouts: int
    runs: int
    earned_runs: int
    era: float
    whip: float


class BattingVsEntry(BaseModel):
    """打者對單一球隊的年度累計成績"""
    opponent: str
    games: int
    plate_appearances: int
    at_bats: int
    hits: int
    doubles: int
    triples: int
    home_runs: int
    rbi: int
    walks: int
    strikeouts: int
    stolen_bases: int
    avg: float
    obp: float
    slg: float
    ops: float


class PitchingVsEntry(BaseModel):
    """投手對單一球隊的年度累計成績"""
    opponent: str
    games: int
    wins: int
    losses: int
    saves: int
    innings_pitched: float
    hits: int
    home_runs: int
    walks: int
    strikeouts: int
    runs: int
    earned_runs: int
    era: float
    whip: float


class PlayerStats(BaseModel):
    """球員成績（有資料的欄位才會有值）"""
    acnt: str
    name: str
    kind_code: str          # 賽制代碼，例如 A=一軍例行賽
    year: int | None        # None 表示生涯累計
    batting: BattingStats | None = None
    pitching: PitchingStats | None = None
    vs_teams: list[BattingVsEntry] | list[PitchingVsEntry] | None = None  # 指定年度才有
