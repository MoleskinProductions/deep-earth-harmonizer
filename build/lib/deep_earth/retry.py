import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Any, Dict, Optional

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), reraise=True)
async def fetch_with_retry(session: aiohttp.ClientSession, url: str, params: Optional[Dict[str, Any]] = None) -> bytes:
    """
    Performs an async GET request with exponential backoff and retries.

    Args:
        session: An active aiohttp client session.
        url: The target URL.
        params: Optional query parameters.

    Returns:
        The response content as bytes.

    Raises:
        aiohttp.ClientResponseError: if the request fails after all retries.
    """
    async with session.get(url, params=params) as response:
        response.raise_for_status()
        return await response.read()
