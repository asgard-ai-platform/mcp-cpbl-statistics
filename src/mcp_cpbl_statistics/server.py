from fastmcp import FastMCP

from mcp_cpbl_statistics.tools import player, schedule, season_standings, toplist

mcp = FastMCP("cpbl-statistics")

season_standings.register(mcp)
toplist.register(mcp)
player.register(mcp)
schedule.register(mcp)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
