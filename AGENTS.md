# AGENTS.md

## Commands

```bash
uv sync                        # install deps (required before anything else)
uv run pytest                  # unit tests only (integration excluded by default)
uv run pytest -m integration   # live tests against cpbl.com.tw (~30s, needs network)
uv run mcp-cpbl-statistics     # run MCP server over stdio
```

## Architecture

- Real entry point: `src/mcp_cpbl_statistics/server.py` — `main.py` in root is an unused stub.
- Each tool group lives in `src/mcp_cpbl_statistics/tools/<group>/tool.py` and exposes a `register(mcp: FastMCP)` function. Adding a new tool = add a module + call `register()` in `server.py`.
- All HTTP is in `scraper/fetcher.py`. Many CPBL endpoints are POST-only JSON APIs that require a CSRF token (`__RequestVerificationToken`) extracted from the preceding GET page. The fetcher handles this automatically via `fetch_html_and_post_json()`.
- `tools/season_standings/` is a dead duplicate of `tools/standings/`; not imported anywhere. Ignore it.

## Models

Key field names that are easy to get wrong:

- `PlayerGameLog.games` (not `.entries`) — list of `BattingGameEntry | PitchingGameEntry`
- `PlayerHeadToHead.opponent_team_name` / `.opponent_team_code` (not `.opponent_team`)
- `PlayerApartStats.groups` — a two-棲 player returns 2 groups with the same `group_id` (one batting, one pitching) when filtered

## Testing

- Unit tests use saved fixtures in `tests/tools/<group>/fixtures/`. No network, fast.
- Integration tests are in `tests/integration/test_tools.py`, marked `@pytest.mark.integration`, excluded by `addopts` in `pyproject.toml`.
- `asyncio_mode = "auto"` is set globally — no need to add `@pytest.mark.asyncio` to async tests.
- Known fixture players: pitcher `0000004626` (王奕凱), fielder `0000001339` (林祖傑), apart-stats `0000003563` (余德龍, two-way).
