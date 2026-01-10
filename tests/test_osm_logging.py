import pytest
import logging
import json
from unittest.mock import MagicMock, AsyncMock, patch
from deep_earth.providers.osm import OverpassAdapter

@pytest.fixture
def mock_cache():
    return MagicMock()

@pytest.mark.asyncio
async def test_osm_logging_cache_hit(mock_cache, caplog):
    adapter = OverpassAdapter()
    adapter.cache = mock_cache
    
    mock_cache.exists.return_value = True
    mock_cache.get_path.return_value = "/tmp/cached_osm.json"
    
    # Create fake file for json.load
    with patch("builtins.open", new_callable=MagicMock) as mock_open:
        mock_file = MagicMock()
        mock_file.read.return_value = '{"elements": []}'
        mock_file.__enter__.return_value = mock_file
        mock_open.return_value = mock_file
        
        # We need to mock json.load as well since we are mocking open
        # Or simpler: just mock json.load
        with patch("json.load", return_value={"elements": []}):
            with caplog.at_level(logging.DEBUG, logger="deep_earth.providers.osm"):
                await adapter.fetch((44.9, -93.1, 45.0, -93.0), resolution=10)
    
    assert "Fetching OSM data" in caplog.text
    assert "Cache hit for" in caplog.text

@pytest.mark.asyncio
async def test_osm_logging_cache_miss(mock_cache, caplog):
    adapter = OverpassAdapter()
    adapter.cache = mock_cache
    
    mock_cache.exists.return_value = False
    
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read = AsyncMock(return_value=b'{"elements": []}')
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = MagicMock()
    mock_session.get.return_value = mock_response
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        with caplog.at_level(logging.DEBUG, logger="deep_earth.providers.osm"):
            await adapter.fetch((44.9, -93.1, 45.0, -93.0), resolution=10)
            
    assert "Cache miss for" in caplog.text
    assert "Fetched OSM data successfully" in caplog.text

@pytest.mark.asyncio
async def test_osm_logging_error(mock_cache, caplog):
    adapter = OverpassAdapter()
    adapter.cache = mock_cache
    
    mock_cache.exists.return_value = False
    
    mock_response = MagicMock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="Internal Server Error")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = MagicMock()
    mock_session.get.return_value = mock_response
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        # Configure raise_for_status to raise
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")

        with caplog.at_level(logging.ERROR, logger="deep_earth.providers.osm"):
            with pytest.raises(Exception):
                await adapter.fetch((44.9, -93.1, 45.0, -93.0), resolution=10)

    assert "Failed to fetch OSM: HTTP Error" in caplog.text