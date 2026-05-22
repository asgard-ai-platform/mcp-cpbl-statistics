from bs4 import BeautifulSoup, Tag

from mcp_cpbl_statistics.models.toplist import TopList, TopListCard, TopListEntry


def _parse_cards(soup: BeautifulSoup) -> list[TopListCard]:
    # 每張卡片是一個無 class 的 div，內含 div.title 和一個 ul
    # 用 div.rank 定位，往上找到卡片根節點
    seen: set[int] = set()
    card_roots: list[Tag] = []
    for rank_div in soup.find_all("div", class_="rank"):
        li = rank_div.find_parent("li")
        if li is None:
            continue
        ul = li.find_parent("ul")
        if ul is None:
            continue
        card = ul.find_parent("div")
        if card is None or id(card) in seen:
            continue
        seen.add(id(card))
        card_roots.append(card)

    cards = []
    for card in card_roots:
        title_div = card.find("div", class_="title")
        if title_div is None:
            continue
        en_span = title_div.find("span", class_="en")
        en = en_span.get_text(strip=True) if en_span else ""
        zh = title_div.get_text(strip=True).replace(en, "").strip()

        entries = []
        for li in card.find_all("li"):
            rank_div = li.find("div", class_="rank")
            player_div = li.find("div", class_="player")
            num_div = li.find("div", class_="num")
            if not (rank_div and player_div and num_div):
                continue
            name_a = player_div.find("a", class_="name")
            team_a = player_div.find("a", class_="team")
            entries.append(TopListEntry(
                rank=int(rank_div.get_text(strip=True)),
                player=name_a.get_text(strip=True) if name_a else "",
                team=team_a.get_text(strip=True).strip("()") if team_a else "",
                value=num_div.get_text(strip=True),
            ))

        cards.append(TopListCard(category_zh=zh, category_en=en, entries=entries))

    return cards


def parse_toplist(html: str) -> TopList:
    """Parse the /stats/toplist page HTML into a TopList model."""
    soup = BeautifulSoup(html, "html.parser")

    h3 = soup.find("h3")
    season_label = h3.get_text(strip=True) if h3 else ""

    return TopList(
        season_label=season_label,
        cards=_parse_cards(soup),
    )
