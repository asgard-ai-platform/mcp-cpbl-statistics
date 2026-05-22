"""Parsers for player profile HTML and stats API JSON responses."""
import json
import re

from bs4 import BeautifulSoup

from mcp_cpbl_statistics.models.player import (
    BattingStats,
    BattingVsEntry,
    PitchingStats,
    PitchingVsEntry,
    PlayerProfile,
    PlayerStats,
)

_HT_WT_RE = re.compile(r"(\d+)")


def _dd(dl, class_name: str) -> str:
    """Get the desc text from a dd with a given class inside a dl."""
    dd = dl.find("dd", class_=class_name)
    if not dd:
        return ""
    desc = dd.find("div", class_="desc")
    return desc.get_text(strip=True) if desc else ""


def parse_player_profile(html: str, acnt: str) -> PlayerProfile:
    """Parse /team/person?acnt=... HTML into a PlayerProfile."""
    soup = BeautifulSoup(html, "html.parser")

    name_div = soup.find("div", class_="name")
    dt = name_div.find_parent("dt") if name_div else None
    dl = dt.find_parent("dl") if dt else None

    if not dl:
        raise ValueError(f"Cannot find player info dl for acnt={acnt}")

    # 姓名 & 背號
    number_span = name_div.find("span", class_="number") if name_div else None
    number = number_span.get_text(strip=True) if number_span else ""
    # 移除背號 span 後取名字
    if number_span:
        number_span.extract()
    name = name_div.get_text(strip=True) if name_div else ""

    # 球隊
    team_div = dt.find("div", class_="team") if dt else None
    team = team_div.get_text(strip=True) if team_div else ""

    # 身高/體重：「186(CM) / 93(KG)」→ 取數字
    ht_wt_raw = _dd(dl, "ht_wt")
    nums = _HT_WT_RE.findall(ht_wt_raw)
    height = int(nums[0]) if len(nums) >= 1 else None
    weight = int(nums[1]) if len(nums) >= 2 else None

    return PlayerProfile(
        acnt=acnt,
        name=name,
        number=number,
        team=team,
        position=_dd(dl, "pos"),
        batting_throwing=_dd(dl, "b_t"),
        height_cm=height,
        weight_kg=weight,
        birthday=_dd(dl, "born"),
        debut=_dd(dl, "debut"),
        education=_dd(dl, "edu"),
        nationality=_dd(dl, "nationality"),
        draft=_dd(dl, "draft"),
    )


def _parse_batting(row: dict, year: int | None = None) -> BattingStats:
    return BattingStats(
        year=year,
        games=row.get("TotalGames") or 0,
        plate_appearances=row.get("PlateAppearances") or 0,
        at_bats=row.get("HitCnt") or 0,         # HitCnt = 打數（打席扣掉保送等）
        hits=row.get("HittingCnt") or 0,
        doubles=row.get("TwoBaseHitCnt") or 0,
        triples=row.get("ThreeBaseHitCnt") or 0,
        home_runs=row.get("HomeRunCnt") or 0,
        rbi=row.get("RunBattedINCnt") or 0,
        runs=row.get("ScoreCnt") or 0,
        strikeouts=row.get("StrikeOutCnt") or 0,
        walks=row.get("BasesONBallsCnt") or 0,
        stolen_bases=row.get("StealBaseOKCnt") or 0,
        avg=row.get("Avg") or 0.0,
        obp=row.get("Obp") or 0.0,
        slg=row.get("Slg") or 0.0,
        ops=row.get("Ops") or 0.0,
    )


def _parse_pitching(row: dict, year: int | None = None) -> PitchingStats:
    return PitchingStats(
        year=year,
        games=row.get("TotalGames") or 0,
        wins=row.get("Wins") or 0,
        losses=row.get("Loses") or 0,
        saves=row.get("SaveOK") or 0,
        holds=row.get("ReliefPointCnt") or 0,
        innings_pitched=row.get("InningPitched") or 0.0,
        hits=row.get("HittingCnt") or 0,
        home_runs=row.get("HomeRunCnt") or 0,
        walks=row.get("BasesONBallsCnt") or 0,
        strikeouts=row.get("StrikeOutCnt") or 0,
        runs=row.get("RunCnt") or 0,
        earned_runs=row.get("EarnedRunCnt") or 0,
        era=row.get("Era") or 0.0,
        whip=row.get("Whip") or 0.0,
    )


def _extract_name(batting_rows: list[dict], pitching_rows: list[dict]) -> str:
    if batting_rows:
        return batting_rows[0].get("Name", "")
    if pitching_rows:
        return pitching_rows[0].get("Name", "")
    return ""


def parse_player_career_stats(
    acnt: str,
    kind_code: str,
    batting_resp: dict,
    pitching_resp: dict,
) -> PlayerStats:
    """Parse getbattingcareerscore + getpitchcareerscore API responses (career totals)."""
    batting_rows: list[dict] = json.loads(batting_resp.get("BattingCareerScore") or "[]")
    pitching_rows: list[dict] = json.loads(pitching_resp.get("PitchCareerScore") or "[]")

    return PlayerStats(
        acnt=acnt,
        name=_extract_name(batting_rows, pitching_rows),
        kind_code=kind_code,
        year=None,
        batting=_parse_batting(batting_rows[0]) if batting_rows else None,
        pitching=_parse_pitching(pitching_rows[0]) if pitching_rows else None,
    )


def _parse_batting_vs(row: dict) -> BattingVsEntry:
    return BattingVsEntry(
        opponent=row.get("FightTeamName", ""),
        games=row.get("TotalGames") or 0,
        plate_appearances=row.get("PlateAppearances") or 0,
        at_bats=row.get("HitCnt") or 0,
        hits=row.get("HittingCnt") or 0,
        doubles=row.get("TwoBaseHitCnt") or 0,
        triples=row.get("ThreeBaseHitCnt") or 0,
        home_runs=row.get("HomeRunCnt") or 0,
        rbi=row.get("RunBattedINCnt") or 0,
        walks=row.get("BasesONBallsCnt") or 0,
        strikeouts=row.get("StrikeOutCnt") or 0,
        stolen_bases=row.get("StealBaseOKCnt") or 0,
        avg=row.get("Avg") or 0.0,
        obp=row.get("Obp") or 0.0,
        slg=row.get("Slg") or 0.0,
        ops=row.get("Ops") or 0.0,
    )


def _parse_pitching_vs(row: dict) -> PitchingVsEntry:
    ip_whole = row.get("InningPitchedCnt") or 0
    ip_thirds = row.get("InningPitchedDiv3Cnt") or 0
    innings_pitched = round(ip_whole + ip_thirds / 3, 2) if (ip_whole or ip_thirds) else (row.get("InningPitched") or 0.0)
    return PitchingVsEntry(
        opponent=row.get("FightTeamName", ""),
        games=row.get("TotalGames") or 0,
        wins=row.get("Wins") or 0,
        losses=row.get("Loses") or 0,
        saves=row.get("SaveOK") or 0,
        innings_pitched=innings_pitched,
        hits=row.get("HittingCnt") or 0,
        home_runs=row.get("HomeRunCnt") or 0,
        walks=row.get("BasesONBallsCnt") or 0,
        strikeouts=row.get("StrikeOutCnt") or 0,
        runs=row.get("RunCnt") or 0,
        earned_runs=row.get("EarnedRunCnt") or 0,
        era=row.get("Era") or 0.0,
        whip=row.get("Whip") or 0.0,
    )


def parse_vs_teams(fighter_resp: dict, is_pitcher: bool) -> list[BattingVsEntry] | list[PitchingVsEntry]:
    """Parse getfighterscore API response into vs_teams list."""
    rows: list[dict] = json.loads(fighter_resp.get("FighterScore") or "[]")
    if not rows:
        return []
    if is_pitcher:
        return [_parse_pitching_vs(r) for r in rows]
    return [_parse_batting_vs(r) for r in rows]


def parse_player_yearly_stats(
    acnt: str,
    kind_code: str,
    year: int,
    batting_resp: dict,
    pitching_resp: dict,
    fighter_resp: dict | None = None,
) -> PlayerStats:
    """Parse getbattingscore + getpitchscore + (optionally) getfighterscore."""
    batting_rows: list[dict] = json.loads(batting_resp.get("BattingScore") or "[]")
    pitching_rows: list[dict] = json.loads(pitching_resp.get("PitchScore") or "[]")

    year_str = str(year)
    batting_row = next((r for r in batting_rows if str(r.get("Year")) == year_str), None)
    pitching_row = next((r for r in pitching_rows if str(r.get("Year")) == year_str), None)

    if batting_row is None and pitching_row is None:
        raise ValueError(f"No stats found for acnt={acnt} year={year} kind_code={kind_code}")

    name = _extract_name(batting_rows, pitching_rows)
    is_pitcher = pitching_row is not None and batting_row is None

    vs_teams = None
    if fighter_resp is not None:
        vs_teams = parse_vs_teams(fighter_resp, is_pitcher) or None

    return PlayerStats(
        acnt=acnt,
        name=name,
        kind_code=kind_code,
        year=year,
        batting=_parse_batting(batting_row, year) if batting_row else None,
        pitching=_parse_pitching(pitching_row, year) if pitching_row else None,
        vs_teams=vs_teams,
    )
