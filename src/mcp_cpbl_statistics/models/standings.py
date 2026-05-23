from pydantic import BaseModel


class TeamStandingRow(BaseModel):
    """一支球隊的勝負戰績列"""
    rank: int
    team: str
    games: int
    wins: int
    draws: int
    losses: int
    pct: float
    gb: str  # 勝差（領先者為 "-"）
    home: str  # 主場戰績，例如 "14-0-5"
    away: str  # 客場戰績


class TeamPitchingRow(BaseModel):
    """一支球隊的團隊投球成績列"""
    team: str
    games: int
    batters_faced: int
    pitches: int
    hits: int
    home_runs: int
    walks: int
    strikeouts: int
    wild_pitches: int
    balks: int
    runs: int
    earned_runs: int
    whip: float
    era: float


class TeamBattingRow(BaseModel):
    """一支球隊的團隊打擊成績列"""
    team: str
    games: int
    at_bats: int
    runs: int
    rbi: int
    hits: int
    home_runs: int
    total_bases: int
    strikeouts: int
    walks: int
    stolen_bases: int
    obp: float  # 上壘率
    slg: float  # 長打率
    avg: float  # 打擊率


class TeamFieldingRow(BaseModel):
    """一支球隊的團隊守備成績列"""
    team: str
    games: int
    chances: int
    putouts: int
    assists: int
    errors: int
    double_plays: int
    triple_plays: int
    pickoffs: int
    passed_balls: int
    cs: int       # 盜壘阻殺
    sb_allowed: int  # 被盜成功
    fpct: float   # 守備率


class SeasonStandings(BaseModel):
    """本季球隊戰績頁面所有資料"""
    season_label: str  # 例如 "2026年 上半季"
    standings: list[TeamStandingRow]
    pitching: list[TeamPitchingRow]
    batting: list[TeamBattingRow]
    fielding: list[TeamFieldingRow]


class HistorySeasonStandings(BaseModel):
    """歷年單一賽段（上半季、下半季或全年）的球隊戰績"""
    label: str                      # 例如「上半季戰績」
    standings: list[TeamStandingRow]


class HistoryStandings(BaseModel):
    """歷年球隊戰績（一個年度）"""
    year: int
    kind_code: str
    seasons: list[HistorySeasonStandings]  # 上半季、下半季、全年
