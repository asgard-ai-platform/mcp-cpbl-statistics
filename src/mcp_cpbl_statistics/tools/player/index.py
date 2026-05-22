"""Internal helper: build a player name → acnt index from /player."""
import re

from bs4 import BeautifulSoup

from mcp_cpbl_statistics.models.player import PlayerIndexEntry
from mcp_cpbl_statistics.scraper.fetcher import fetch_html

_URL = "https://cpbl.com.tw/player"
# 前綴符號：* ＃ ◎ # 等，清掉後取名字
_NAME_PREFIX_RE = re.compile(r"^[*＃◎#✽]+")


def _clean_name(raw: str) -> str:
    return _NAME_PREFIX_RE.sub("", raw).strip()


async def fetch_player_index() -> list[PlayerIndexEntry]:
    """Fetch /player and return all active players as a list of PlayerIndexEntry."""
    html = await fetch_html(_URL)
    soup = BeautifulSoup(html, "html.parser")

    entries: list[PlayerIndexEntry] = []
    for players_div in soup.find_all("div", class_="PlayersList"):
        dl = players_div.find("dl")
        if not dl:
            continue
        dt = dl.find("dt")
        team = dt.get_text(strip=True) if dt else ""
        for dd in dl.find_all("dd"):
            a = dd.find("a")
            if not a:
                continue
            href = a.get("href", "")
            m = re.search(r"acnt=(\d+)", href)
            if not m:
                continue
            entries.append(PlayerIndexEntry(
                acnt=m.group(1),
                name=_clean_name(a.get_text(strip=True)),
                team=team,
            ))
    return entries
