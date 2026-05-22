import re

import httpx

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}

_CSRF_RE = re.compile(r"RequestVerificationToken:\s*['\"]([^'\"]+)['\"]")


async def fetch_html(url: str) -> str:
    """Fetch a URL and return the raw HTML string."""
    async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


async def fetch_html_and_post_json(page_url: str, api_path: str, data: dict) -> dict:
    """Fetch a page to obtain cookie + CSRF token, then POST to an API on the same origin.

    Returns the parsed JSON response dict.
    """
    async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
        # Step 1: load the page — sets session cookie automatically
        page_resp = await client.get(page_url)
        page_resp.raise_for_status()

        # Step 2: extract CSRF token embedded in the page JS
        m = _CSRF_RE.search(page_resp.text)
        if not m:
            raise ValueError(f"Cannot find RequestVerificationToken in {page_url}")
        token = m.group(1)

        # Step 3: POST to the API
        url = page_resp.url
        origin = f"{url.scheme}://{url.host}"  # e.g. https://cpbl.com.tw
        api_url = origin + api_path
        api_resp = await client.post(
            api_url,
            data=data,
            headers={
                "RequestVerificationToken": token,
                "X-Requested-With": "XMLHttpRequest",
                "Referer": page_url,
            },
        )
        api_resp.raise_for_status()
        return api_resp.json()
