from fastmcp import FastMCP

from mcp_cpbl_statistics.tools import season_standings

mcp = FastMCP("cpbl-statistics")

season_standings.register(mcp)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
