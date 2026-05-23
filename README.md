# MCP CPBL Statistics

An MCP server for CPBL (Chinese Professional Baseball League / 中華職棒) statistics, exposing AI-callable tools over [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

## Features

- **stdio JSON-RPC 2.0** — Standard MCP transport protocol
- **`@mcp.tool()` decorator** — Pydantic-typed tool registration
- **Web scraper** — HTML scraping and XHR JSON API calls against `cpbl.com.tw`
- **No-auth public access** — No API keys required; CSRF token handling is automatic
- **Fixture-based unit tests** — Fast offline test suite with saved HTML/JSON fixtures
- **Integration tests** — Live end-to-end tests against `cpbl.com.tw`, opt-in via `-m integration`

## Requirements

- Python `>=3.12` (developed on `3.14`)
- `uv`

## Available Tools

### Standings

- `get_season_standings` — Get current season team standings (W/L record, pitching, batting, fielding)
- `get_history_standings` — Get historical standings for a given year (first half / second half / full season)

### Top Lists

- `get_toplist` — Get the season top-5 leaderboards for ERA, W, SV, HLD, SO, AVG, H, HR, RBI, SB

### Players

- `search_players` — Search active players by name (partial match); returns player ID (`acnt`), name, team
- `get_player_profile` — Get player profile: jersey number, position, batting/throwing hand, height/weight, birthday, first appearance, education, draft
- `get_player_stats` — Get career or single-season batting/pitching stats for a player
- `get_player_apart_stats` — Get player split stats (home/away, vs. opponent, lineup position, runners on base, inning, score situation, month, stadium, etc.)
- `get_player_game_log` — Get per-game log for a player, optionally filtered by year or last N games
- `get_player_headtohead` — Get head-to-head matchup stats for a player against a specific team

### Schedule

- `get_schedule` — Query game schedule / results, filterable by year, month, team, and game type; finished games include score, W/L/SV pitchers, and MVP

### `kind_code` values (shared across tools)

| Code | Description |
|------|-------------|
| `A`  | 一軍例行賽 (1st team regular season, **default**) |
| `B`  | 一軍明星賽 (All-Star game) |
| `C`  | 一軍總冠軍賽 (Championship series) |
| `D`  | 二軍例行賽 (2nd team) |
| `E`  | 一軍季後挑戰賽 (Postseason challenger) |
| `G`  | 一軍熱身賽 (Spring training) |

## Quick Start

```bash
# Install dependencies
uv sync

# Run server (stdio transport)
uv run mcp-cpbl-statistics
```

## MCP Client Configuration

The repository includes a `.mcp.json` for local use:

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

MIT License — see [LICENSE](LICENSE) for details.
