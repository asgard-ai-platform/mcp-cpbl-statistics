import re

from bs4 import BeautifulSoup, Tag

from mcp_cpbl_statistics.models.standings import (
    SeasonStandings,
    TeamBattingRow,
    TeamFieldingRow,
    TeamPitchingRow,
    TeamStandingRow,
)


def _text(cell: Tag) -> str:
    return cell.get_text(strip=True)


def _float_or(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _int_or(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _parse_season_label(soup: BeautifulSoup) -> str:
    tag = soup.select_one("h3")
    return tag.get_text(strip=True) if tag else ""


def _parse_standings(rows: list[Tag]) -> list[TeamStandingRow]:
    # 欄位順序（16 cells）：
    # [0] rank+team合併  [1] 出賽  [2] 勝-和-敗  [3] 勝率  [4] 勝差
    # [5] 淘汰指數  [6..11] 對戰細格  [12] 主場  [13] 客場
    # [14] 連勝/連敗  [15] 近十場
    result = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 14:
            continue
        rank_team = _text(cells[0])
        # rank_team 格式為 "1味全龍"
        m = re.match(r"^(\d+)(.+)$", rank_team)
        if not m:
            continue
        rank = int(m.group(1))
        team = m.group(2).strip()

        wld = _text(cells[2]).split("-")
        wins = _int_or(wld[0]) if len(wld) == 3 else 0
        draws = _int_or(wld[1]) if len(wld) == 3 else 0
        losses = _int_or(wld[2]) if len(wld) == 3 else 0

        result.append(TeamStandingRow(
            rank=rank,
            team=team,
            games=_int_or(_text(cells[1])),
            wins=wins,
            draws=draws,
            losses=losses,
            pct=_float_or(_text(cells[3])),
            gb=_text(cells[4]),
            home=_text(cells[12]),
            away=_text(cells[13]),
        ))
    return result


def _parse_pitching(rows: list[Tag]) -> list[TeamPitchingRow]:
    result = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 14:
            continue
        team = _text(cells[0])
        if not team:
            continue
        result.append(TeamPitchingRow(
            team=team,
            games=_int_or(_text(cells[1])),
            batters_faced=_int_or(_text(cells[2])),
            pitches=_int_or(_text(cells[3])),
            hits=_int_or(_text(cells[4])),
            home_runs=_int_or(_text(cells[5])),
            walks=_int_or(_text(cells[6])),
            strikeouts=_int_or(_text(cells[7])),
            wild_pitches=_int_or(_text(cells[8])),
            balks=_int_or(_text(cells[9])),
            runs=_int_or(_text(cells[10])),
            earned_runs=_int_or(_text(cells[11])),
            whip=_float_or(_text(cells[12])),
            era=_float_or(_text(cells[13])),
        ))
    return result


def _parse_batting(rows: list[Tag]) -> list[TeamBattingRow]:
    result = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 13:
            continue
        team = _text(cells[0])
        if not team:
            continue
        result.append(TeamBattingRow(
            team=team,
            games=_int_or(_text(cells[1])),
            at_bats=_int_or(_text(cells[2])),
            runs=_int_or(_text(cells[3])),
            rbi=_int_or(_text(cells[4])),
            hits=_int_or(_text(cells[5])),
            home_runs=_int_or(_text(cells[6])),
            total_bases=_int_or(_text(cells[7])),
            strikeouts=_int_or(_text(cells[8])),
            walks=_int_or(_text(cells[9])),
            stolen_bases=_int_or(_text(cells[10])),
            obp=_float_or(_text(cells[11])),
            slg=_float_or(_text(cells[12])),
            avg=_float_or(_text(cells[13])) if len(cells) > 13 else 0.0,
        ))
    return result


def _parse_fielding(rows: list[Tag]) -> list[TeamFieldingRow]:
    result = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 12:
            continue
        team = _text(cells[0])
        if not team:
            continue
        result.append(TeamFieldingRow(
            team=team,
            games=_int_or(_text(cells[1])),
            chances=_int_or(_text(cells[2])),
            putouts=_int_or(_text(cells[3])),
            assists=_int_or(_text(cells[4])),
            errors=_int_or(_text(cells[5])),
            double_plays=_int_or(_text(cells[6])),
            triple_plays=_int_or(_text(cells[7])),
            pickoffs=_int_or(_text(cells[8])),
            passed_balls=_int_or(_text(cells[9])),
            cs=_int_or(_text(cells[10])),
            sb_allowed=_int_or(_text(cells[11])),
            fpct=_float_or(_text(cells[12])) if len(cells) > 12 else 0.0,
        ))
    return result


def parse_season_standings(html: str) -> SeasonStandings:
    """Parse the /standings/season page HTML into a SeasonStandings model."""
    soup = BeautifulSoup(html, "html.parser")
    season_label = _parse_season_label(soup)

    # 頁面有 4 個 table，依序為：戰績、投球、打擊、守備
    tables = soup.find_all("table")
    if len(tables) < 4:
        raise ValueError(f"Expected at least 4 tables, got {len(tables)}")

    def body_rows(table: Tag) -> list[Tag]:
        tbody = table.find("tbody")
        return tbody.find_all("tr") if tbody else table.find_all("tr")[1:]

    return SeasonStandings(
        season_label=season_label,
        standings=_parse_standings(body_rows(tables[0])),
        pitching=_parse_pitching(body_rows(tables[1])),
        batting=_parse_batting(body_rows(tables[2])),
        fielding=_parse_fielding(body_rows(tables[3])),
    )
