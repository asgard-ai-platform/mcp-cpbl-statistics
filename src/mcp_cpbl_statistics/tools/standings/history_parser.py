"""Parser for /standings/historyaction HTML fragment response."""
import re

from bs4 import BeautifulSoup, Tag

from mcp_cpbl_statistics.models.standings import (
    HistorySeasonStandings,
    HistoryStandings,
    TeamStandingRow,
)

_RANK_TEAM_RE = re.compile(r"^(\d+)(.+)$")


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


def _text(cell: Tag) -> str:
    return cell.get_text(strip=True)


def _parse_history_standings(rows: list[Tag]) -> list[TeamStandingRow]:
    """Parse history standings rows.

    History table columns:
    [0] rank+team  [1] games  [2] W-D-L  [3] pct  [4] gb
    [5..N-3] head-to-head vs each team (varies by era: 4–6 teams)
    [-2] home  [-1] away
    Minimum meaningful size: 5 fixed + 2 home/away + at least 1 h2h = 8 cells.
    """
    result = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 8:
            continue
        m = _RANK_TEAM_RE.match(_text(cells[0]))
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
            home=_text(cells[-2]),
            away=_text(cells[-1]),
        ))
    return result


def parse_history_standings(html_fragment: str, year: int, kind_code: str) -> HistoryStandings:
    """Parse the HTML fragment returned by /standings/historyaction.

    The fragment contains up to 3 sections (上半季/下半季/全年), each with a
    RecordTableWrap div containing a caption and a standings table.
    """
    soup = BeautifulSoup(html_fragment, "html.parser")

    seasons: list[HistorySeasonStandings] = []
    for wrap in soup.find_all("div", class_="RecordTableWrap"):
        caption_div = wrap.find(class_="record_table_caption")
        if not caption_div:
            continue
        label = caption_div.get_text(strip=True)

        table = wrap.find("table")
        if not table:
            continue

        tbody = table.find("tbody")
        rows: list[Tag] = tbody.find_all("tr") if tbody else table.find_all("tr")[1:]

        standing_rows = _parse_history_standings(rows)
        if standing_rows:
            seasons.append(HistorySeasonStandings(label=label, standings=standing_rows))

    return HistoryStandings(year=year, kind_code=kind_code, seasons=seasons)
