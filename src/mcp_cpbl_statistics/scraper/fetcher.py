import httpx

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}


async def fetch_html(url: str) -> str:
    """Fetch a URL and return the raw HTML string."""
    async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text
