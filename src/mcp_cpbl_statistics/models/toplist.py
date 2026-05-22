from pydantic import BaseModel


class TopListEntry(BaseModel):
    """單一排行榜的一筆資料"""
    rank: int
    player: str
    team: str
    value: str  # 原始數值字串，避免因類別不同（率/次數）需要轉型


class TopListCard(BaseModel):
    """單一排行榜卡片（一個統計類別的 Top 5）"""
    category_zh: str   # 中文名稱，例如「防禦率」
    category_en: str   # 英文縮寫，例如「ERA」
    entries: list[TopListEntry]


class TopList(BaseModel):
    """單項排行榜頁面全部資料"""
    season_label: str          # 例如 "2026年 單項排行榜"
    cards: list[TopListCard]
