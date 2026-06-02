# MCP CPBL Statistics

[![PyPI version](https://img.shields.io/pypi/v/mcp-cpbl-statistics)](https://pypi.org/project/mcp-cpbl-statistics/)
[![Python versions](https://img.shields.io/pypi/pyversions/mcp-cpbl-statistics)](https://pypi.org/project/mcp-cpbl-statistics/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/asgard-ai-platform/mcp-cpbl-statistics)](https://github.com/asgard-ai-platform/mcp-cpbl-statistics/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/asgard-ai-platform/mcp-cpbl-statistics)](https://github.com/asgard-ai-platform/mcp-cpbl-statistics/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/asgard-ai-platform/mcp-cpbl-statistics)](https://github.com/asgard-ai-platform/mcp-cpbl-statistics/commits/main)
[![MCP](https://img.shields.io/badge/MCP-compatible-blue)](https://modelcontextprotocol.io/)

[繁體中文](README.zh-TW.md)

An MCP server for CPBL (Chinese Professional Baseball League / 中華職棒) statistics, exposing AI-callable tools over [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

## What This Does

- **10 ready-to-use tools** covering team standings, player profiles, batting/pitching stats, game logs, head-to-head matchups, top-5 leaderboards, and game schedules
- **MCP server (stdio JSON-RPC 2.0)** — plug into Claude Code and start asking about CPBL instantly
- **Web scraper** — HTML scraping and XHR JSON API calls against `cpbl.com.tw`
- **No-auth public access** — No API keys required; CSRF token handling is automatic
- **Fixture-based unit tests** — Fast offline test suite with saved HTML/JSON fixtures
- **Integration tests** — Live end-to-end tests against `cpbl.com.tw`, opt-in via `-m integration`

---

## Quick Start

### Install

```bash
pip install mcp-cpbl-statistics
```

Or with uv:

```bash
uv sync
```

### Use with Claude Code

```bash
claude mcp add --transport stdio cpbl-statistics -- mcp-cpbl-statistics
```

### Use with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "cpbl-statistics": {
      "command": "uv",
      "args": ["run", "mcp-cpbl-statistics"]
    }
  }
}
```

Or with pip:

```json
{
  "mcpServers": {
    "cpbl-statistics": {
      "command": "mcp-cpbl-statistics"
    }
  }
}
```

---

## Tools (10)

### Standings

| Tool | Description |
|------|-------------|
| `get_season_standings` | Current season team standings (W/L record, pitching, batting, fielding) |
| `get_history_standings` | Historical standings for a given year (first half / second half / full season) |

### Top Lists

| Tool | Description |
|------|-------------|
| `get_toplist` | Season top-5 leaderboards for ERA, W, SV, HLD, SO, AVG, H, HR, RBI, SB |

### Players

| Tool | Description |
|------|-------------|
| `search_players` | Search active players by name (partial match); returns player ID, name, team |
| `get_player_profile` | Player profile: jersey number, position, batting/throwing hand, height/weight, birthday, first appearance, education, draft |
| `get_player_stats` | Career or single-season batting/pitching stats for a player |
| `get_player_apart_stats` | Split stats (home/away, vs. opponent, lineup position, runners on base, inning, score situation, month, stadium, etc.) |
| `get_player_game_log` | Per-game log for a player, optionally filtered by year or last N games |
| `get_player_headtohead` | Head-to-head matchup stats for a player against a specific team |

### Schedule

| Tool | Description |
|------|-------------|
| `get_schedule` | Game schedule / results, filterable by year, month, team, and game type; finished games include score, W/L/SV pitchers, and MVP |

### `kind_code` values (shared across tools)

| Code | Description |
|------|-------------|
| `A` | 一軍例行賽 (1st team regular season, **default**) |
| `B` | 一軍明星賽 (All-Star game) |
| `C` | 一軍總冠軍賽 (Championship series) |
| `D` | 二軍例行賽 (2nd team) |
| `E` | 一軍季後挑戰賽 (Postseason challenger) |
| `G` | 一軍熱身賽 (Spring training) |

---

## Project Structure

```
mcp-cpbl-statistics/
├── main.py                              # Stub entry point (unused)
├── pyproject.toml                       # Project metadata & scripts
├── .mcp.json                            # Local MCP server config
│
└── src/mcp_cpbl_statistics/
    ├── server.py                        # FastMCP server, registers all tools
    ├── scraper/
    │   └── fetcher.py                   # HTTP client (HTML scraping + JSON POST APIs)
    ├── models/                          # Pydantic output models
    │   ├── standings.py
    │   ├── toplist.py
    │   ├── player.py
    │   ├── apart.py
    │   ├── game_log.py
    │   ├── headtohead.py
    │   ├── schedule.py
    │   └── teams.py                     # Team code registry
    └── tools/                           # MCP tool implementations
        ├── standings/                   # get_season_standings, get_history_standings
        ├── toplist/                     # get_toplist
        ├── player/                      # search_players, get_player_*, ...
        └── schedule/                    # get_schedule
```

## Testing

Unit tests run against saved HTML/JSON fixtures (no live network calls required):

```bash
uv run pytest
```

Integration tests make live requests to `cpbl.com.tw` and are excluded by default:

```bash
uv run pytest -m integration
```

## Data Source

All data is scraped from the official CPBL website ([cpbl.com.tw](https://cpbl.com.tw)). No API keys are required. The scraper handles CSRF token extraction automatically for POST-based JSON APIs.

## License

MIT
