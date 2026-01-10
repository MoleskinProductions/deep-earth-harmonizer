import pytest
import logging
from unittest.mock import MagicMock, AsyncMock, patch
from deep_earth.providers.srtm import SRTMAdapter
from deep_earth.coordinates import CoordinateManager

@pytest.fixture
def mock_credentials():
    mock = MagicMock()
    mock.get_opentopography_key.return_value = "test_key"
    return mock

@pytest.fixture
def mock_cache():
    return MagicMock()

@pytest.fixture
def coordinate_manager():
    return CoordinateManager(lat_min=44.9, lat_max=45.1, lon_min=-93.1, lon_max=-92.9)

@pytest.mark.asyncio
async def test_srtm_logging_cache_hit(mock_credentials, mock_cache, coordinate_manager, caplog):
    adapter = SRTMAdapter(mock_credentials, mock_cache)
    
    mock_cache.exists.return_value = True
    mock_cache.get_path.return_value = "/tmp/cached_srtm.tif"
    
    with caplog.at_level(logging.DEBUG, logger="deep_earth.providers.srtm"):
        await adapter.fetch(coordinate_manager, resolution=30)
    
    # We check for partial match in captured logs
    assert "Fetching SRTM for bbox" in caplog.text
    assert "Cache hit for" in caplog.text

@pytest.mark.asyncio
async def test_srtm_logging_cache_miss(mock_credentials, mock_cache, coordinate_manager, caplog):
    adapter = SRTMAdapter(mock_credentials, mock_cache)
    
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read = AsyncMock(return_value=b"data")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = MagicMock()
    mock_session.get.return_value = mock_response
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    mock_cache.exists.return_value = False
    mock_cache.save.return_value = "/tmp/cached_srtm.tif"

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with caplog.at_level(logging.DEBUG, logger="deep_earth.providers.srtm"):
            await adapter.fetch(coordinate_manager, resolution=30)
    
    assert "Cache miss for" in caplog.text
    assert "Fetched SRTM successfully" in caplog.text

@pytest.mark.asyncio
async def test_srtm_logging_error(mock_credentials, mock_cache, coordinate_manager, caplog):
    adapter = SRTMAdapter(mock_credentials, mock_cache)
    
    mock_response = MagicMock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="Server Error")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = MagicMock()
    mock_session.get.return_value = mock_response
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    mock_cache.exists.return_value = False

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with caplog.at_level(logging.ERROR, logger="deep_earth.providers.srtm"):
            with pytest.raises(Exception):
                await adapter.fetch(coordinate_manager, resolution=30)
    
    assert "Failed to fetch SRTM: 500 - Server Error" in caplog.text
