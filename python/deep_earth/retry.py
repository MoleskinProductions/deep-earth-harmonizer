from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
import aiohttp
import logging

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type(aiohttp.ClientError),
    reraise=True,
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
async def fetch_with_retry(session: aiohttp.ClientSession, url: str, **kwargs) -> bytes:
    """
    Fetches URL with retry logic for network errors and 429/5xx responses.
    """
    async with session.get(url, **kwargs) as response:
        # Raise for 4xx/5xx
        response.raise_for_status()
        return await response.read()
