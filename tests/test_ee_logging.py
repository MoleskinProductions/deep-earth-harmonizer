import pytest
import logging
from unittest.mock import patch, MagicMock, AsyncMock
from deep_earth.providers.earth_engine import EarthEngineAdapter
from deep_earth.region import RegionContext as CoordinateManager

@pytest.fixture
def mock_credentials():
    mock = MagicMock()
    mock.get_ee_service_account.return_value = "test@appspot.gserviceaccount.com"
    mock.get_ee_key_file.return_value = "/tmp/key.json"
    return mock

@pytest.fixture
def mock_cache():
    return MagicMock()

@pytest.fixture
def coordinate_manager():
    return CoordinateManager(lat_min=44.97, lat_max=44.98, lon_min=-93.27, lon_max=-93.26)

@pytest.mark.asyncio
async def test_ee_logging_cache_hit(mock_credentials, mock_cache, coordinate_manager, caplog):
    with patch("ee.ServiceAccountCredentials"), patch("ee.Initialize"):
        adapter = EarthEngineAdapter(mock_credentials, mock_cache)
        
        mock_cache.exists.return_value = True
        mock_cache.get_path.return_value = "/tmp/cached_ee.tif"
        
        with caplog.at_level(logging.DEBUG, logger="deep_earth.providers.earth_engine"):
            await adapter.fetch(coordinate_manager, resolution=10)
        
        assert "Fetching EarthEngine data" in caplog.text
        assert "Cache hit for" in caplog.text

@pytest.mark.asyncio
async def test_ee_logging_cache_miss(mock_credentials, mock_cache, coordinate_manager, caplog):
    with patch("ee.ServiceAccountCredentials"), patch("ee.Initialize"):
        adapter = EarthEngineAdapter(mock_credentials, mock_cache)
        
        mock_cache.exists.return_value = False
        
        with patch("ee.ImageCollection") as mock_coll_cls:
            with patch("ee.Geometry.Rectangle"):
                mock_collection = MagicMock()
                mock_coll_cls.return_value = mock_collection
                mock_collection.filterDate.return_value = mock_collection
                mock_collection.size.return_value.getInfo.return_value = 1
                mock_collection.mosaic.return_value.clip.return_value.reproject.return_value = MagicMock()
                
                # Mock export
                with patch.object(adapter, "_fetch_direct", return_value="/tmp/exported.tif"):
                    with caplog.at_level(logging.DEBUG, logger="deep_earth.providers.earth_engine"):
                        await adapter.fetch(coordinate_manager, resolution=10)
        
        assert "Cache miss for" in caplog.text