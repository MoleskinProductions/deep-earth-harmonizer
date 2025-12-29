import pytest
import aiohttp
import numpy as np
from unittest.mock import AsyncMock, patch, MagicMock
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
async def test_srtm_fetch_success(mock_credentials, mock_cache, coordinate_manager):
    adapter = SRTMAdapter(mock_credentials, mock_cache)
    
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read = AsyncMock(return_value=b"fake_geotiff_data")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = MagicMock()
    mock_session.get.return_value = mock_response
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        # Key not in cache
        mock_cache.exists.return_value = False
        mock_cache.save.return_value = "/tmp/cached_srtm.tif"
        
        result_path = await adapter.fetch(coordinate_manager, resolution=30)
        
        assert result_path == "/tmp/cached_srtm.tif"
        mock_cache.save.assert_called_once_with(
            adapter.get_cache_key(coordinate_manager, 30),
            b"fake_geotiff_data",
            category="srtm"
        )

@pytest.mark.asyncio
async def test_srtm_fetch_cache_hit(mock_credentials, mock_cache, coordinate_manager):
    adapter = SRTMAdapter(mock_credentials, mock_cache)
    
    mock_cache.exists.return_value = True
    mock_cache.get_path.return_value = "/tmp/cached_srtm.tif"
    
    result_path = await adapter.fetch(coordinate_manager, resolution=30)
    
    assert result_path == "/tmp/cached_srtm.tif"
    # Should not call aiohttp or save
    mock_cache.save.assert_not_called()

@pytest.mark.asyncio
async def test_srtm_fetch_failure(mock_credentials, mock_cache, coordinate_manager):
    adapter = SRTMAdapter(mock_credentials, mock_cache)
    
    # Setup mock response for failure
    mock_response = MagicMock()
    mock_response.status = 403
    mock_response.text = AsyncMock(return_value="Forbidden")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = MagicMock()
    mock_session.get.return_value = mock_response
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        mock_cache.exists.return_value = False
        with pytest.raises(Exception, match="Failed to fetch SRTM"):
            await adapter.fetch(coordinate_manager, resolution=30)

def test_srtm_transform_to_grid(mock_credentials, mock_cache):
    adapter = SRTMAdapter(mock_credentials, mock_cache)
    
    # Mock rasterio
    mock_src = MagicMock()
    mock_src.read.return_value = np.zeros((10, 10))
    
    with patch("rasterio.open", return_value=mock_src):
        mock_src.__enter__.return_value = mock_src
        result = adapter.transform_to_grid("dummy.tif", None)
        assert isinstance(result, np.ndarray)
        assert result.shape == (10, 10)
