# MCP 中華職棒統計

一個中華職棒（CPBL）統計資料的 MCP 伺服器，透過 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 將資料查詢功能以 AI 可呼叫工具的形式對外開放。

## 功能特色

- **stdio JSON-RPC 2.0** — 標準 MCP 傳輸協定
- **`@mcp.tool()` 裝飾器** — Pydantic 型別化工具註冊
- **網頁爬蟲** — 針對 `cpbl.com.tw` 的 HTML 解析與 XHR JSON API 呼叫
- **免認證公開存取** — 無需 API 金鑰；CSRF token 自動處理
- **Fixture 單元測試** — 使用已儲存的 HTML/JSON fixture，可離線快速執行
- **整合測試** — 對 `cpbl.com.tw` 進行端對端即時測試，透過 `-m integration` 選擇性執行

## 環境需求

- Python `>=3.12`（開發環境使用 `3.14`）
- `uv`

## 可用工具

目前這個伺服器共提供 10 個 MCP tool。

### 戰績

- `get_season_standings` — 取得本季球隊戰績（勝負戰績、投球、打擊、守備）
- `get_history_standings` — 取得指定年度的歷年戰績（上半季／下半季／全年）

### 單項排行

- `get_toplist` — 取得年度單項排行榜前五名（ERA、W、SV、HLD、SO、AVG、H、HR、RBI、SB）

### 球員

- `search_players` — 依姓名搜尋現役球員（支援部分匹配）；回傳球員 ID（`acnt`）、姓名、球隊
- `get_player_profile` — 取得球員基本資料：背號、位置、投打習慣、身高體重、生日、初出場、學歷、選秀
- `get_player_stats` — 取得球員生涯累計或單一年度的打擊／投球成績
- `get_player_apart_stats` — 取得球員分項成績（主客場、對戰對象、打序、壘上跑者、局數、比分情況、月份、球場等）
- `get_player_game_log` — 取得球員逐場成績，可依年度或最近 N 場篩選
- `get_player_headtohead` — 取得球員對特定球隊的投打對決累計成績

### 賽程

- `get_schedule` — 查詢賽程與比賽結果，可依年度、月份、球隊、賽制篩選；已結束的比賽包含比分、勝投／敗投／救援投手及 MVP

### `kind_code` 賽制代碼（各工具共用）

| 代碼 | 說明 |
|------|------|
| `A`  | 一軍例行賽（**預設**） |
| `B`  | 一軍明星賽 |
| `C`  | 一軍總冠軍賽 |
| `D`  | 二軍例行賽 |
| `E`  | 一軍季後挑戰賽 |
| `G`  | 一軍熱身賽 |

## 快速開始

```bash
# 安裝相依套件
uv sync

# 啟動伺服器（stdio 傳輸）
uv run mcp-cpbl-statistics
```

## MCP 客戶端設定

專案內附 `.mcp.json` 供本機使用：

```json
{
  "mcpServers": {
    "cpbl-statistics": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "mcp-cpbl-statistics"]
    }
  }
}
```

## 專案結構

```
mcp-cpbl-statistics/
├── main.py                              # 進入點存根（未使用）
├── pyproject.toml                       # 專案設定與腳本
├── .mcp.json                            # 本機 MCP 伺服器設定
│
└── src/mcp_cpbl_statistics/
    ├── server.py                        # FastMCP 伺服器，註冊所有工具
    ├── scraper/
    │   └── fetcher.py                   # HTTP 客戶端（HTML 解析 + JSON POST API）
    ├── models/                          # Pydantic 輸出模型
    │   ├── standings.py
    │   ├── toplist.py
    │   ├── player.py
    │   ├── apart.py
    │   ├── game_log.py
    │   ├── headtohead.py
    │   ├── schedule.py
    │   └── teams.py                     # 球隊代碼對照表
    └── tools/                           # MCP 工具實作
        ├── standings/                   # get_season_standings, get_history_standings
        ├── toplist/                     # get_toplist
        ├── player/                      # search_players, get_player_*, ...
        └── schedule/                    # get_schedule
```

## 測試

單元測試使用已儲存的 HTML/JSON fixture，不需要網路連線：

```bash
uv run pytest
```

整合測試會對 `cpbl.com.tw` 發出即時請求，預設不執行：

```bash
uv run pytest -m integration
```

## 資料來源

所有資料均爬取自中華職棒官方網站（[cpbl.com.tw](https://cpbl.com.tw)）。無需 API 金鑰，爬蟲會自動處理 POST API 所需的 CSRF token。

## 授權

MIT License — 詳見 [LICENSE](LICENSE)。
