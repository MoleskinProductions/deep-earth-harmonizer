import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

# Ensure import works (will fail initially)
try:
    from deep_earth.retry import fetch_with_retry
except ImportError:
    pass

@pytest.mark.asyncio
async def test_fetch_retry_success():
    from deep_earth.retry import fetch_with_retry
    
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read = AsyncMock(return_value=b"success")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session.get.return_value = mock_response
    
    result = await fetch_with_retry(mock_session, "http://test.com")
    assert result == b"success"
    assert mock_session.get.call_count == 1

@pytest.mark.asyncio
async def test_fetch_retry_failure_then_success():
    from deep_earth.retry import fetch_with_retry
    
    mock_session = MagicMock()
    
    # Fail twice, then succeed
    fail_response = MagicMock()
    fail_response.status = 500
    fail_response.raise_for_status.side_effect = aiohttp.ClientError("Server Error")
    fail_response.__aenter__ = AsyncMock(return_value=fail_response)
    fail_response.__aexit__ = AsyncMock(return_value=None)

    success_response = MagicMock()
    success_response.status = 200
    success_response.read = AsyncMock(return_value=b"success")
    success_response.__aenter__ = AsyncMock(return_value=success_response)
    success_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session.get.side_effect = [fail_response, fail_response, success_response]
    
    # We need to mock wait to speed up test
    with patch("asyncio.sleep"): 
        result = await fetch_with_retry(mock_session, "http://test.com")
    
    assert result == b"success"
    assert mock_session.get.call_count == 3

@pytest.mark.asyncio
async def test_fetch_retry_give_up():
    from deep_earth.retry import fetch_with_retry
    import tenacity
    
    mock_session = MagicMock()
    
    fail_response = MagicMock()
    fail_response.status = 500
    fail_response.raise_for_status.side_effect = aiohttp.ClientError("Server Error")
    fail_response.__aenter__ = AsyncMock(return_value=fail_response)
    fail_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session.get.return_value = fail_response
    
    with patch("asyncio.sleep"):
        with pytest.raises(aiohttp.ClientError):
            await fetch_with_retry(mock_session, "http://test.com")
            
    # Should be 3 attempts
    assert mock_session.get.call_count == 3
