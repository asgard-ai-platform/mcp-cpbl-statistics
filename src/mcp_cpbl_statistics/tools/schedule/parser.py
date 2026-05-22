"""Parser for /schedule/getgamedatas API JSON response."""
import json

from mcp_cpbl_statistics.models.schedule import GameResult


def _game_status(raw: dict) -> str:
    """Determine game status from API fields.

    PresentStatus: 1=finished, 0=not yet played
    IsGameStop: "1"=cancelled/postponed, "0"=normal
    """
    if raw.get("IsGameStop") == "1":
        return "cancelled"
    if raw.get("PresentStatus") == 1:
        return "finished"
    return "scheduled"


def _date(raw_dt: str) -> str:
    """'2026-03-28T00:00:00' → '2026-03-28'"""
    return raw_dt[:10] if raw_dt else ""


def _time(raw_dt: str | None) -> str:
    """'2026-03-28T17:05:00' → '17:05'"""
    if not raw_dt:
        return ""
    parts = raw_dt.split("T")
    return parts[1][:5] if len(parts) == 2 else ""


def _parse_game(raw: dict) -> GameResult:
    status = _game_status(raw)
    return GameResult(
        game_no=raw.get("GameSno") or 0,
        game_date=_date(raw.get("GameDate", "")),
        game_time=_time(raw.get("PreExeDate")),
        kind_code=raw.get("KindCode", ""),
        visiting_team=raw.get("VisitingTeamName", ""),
        home_team=raw.get("HomeTeamName", ""),
        field=raw.get("FieldAbbe", ""),
        status=status,
        visiting_score=raw.get("VisitingScore") if status == "finished" else None,
        home_score=raw.get("HomeScore") if status == "finished" else None,
        winning_pitcher=raw.get("WinningPitcherName", "") if status == "finished" else "",
        losing_pitcher=raw.get("LoserPitcherName", "") if status == "finished" else "",
        closer=raw.get("CloserName", "") if status == "finished" else "",
        mvp=raw.get("MvpName", "") if status == "finished" else "",
    )


def parse_schedule(
    api_resp: dict,
    month: int | None = None,
    team: str | None = None,
) -> list[GameResult]:
    """Parse getgamedatas API response and apply optional filters.

    Args:
        api_resp: raw JSON dict from the API
        month: filter to this month (1-12), or None for all
        team: filter by team name (partial match on visiting or home team)
    """
    raw_games: list[dict] = json.loads(api_resp.get("GameDatas") or "[]")

    games = [_parse_game(g) for g in raw_games]

    if month is not None:
        games = [g for g in games if g.game_date[5:7] == f"{month:02d}"]

    if team is not None:
        t = team.strip()
        games = [
            g for g in games
            if t in g.visiting_team or t in g.home_team
        ]

    return games
