import pytest
import ee
from unittest.mock import patch, MagicMock
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
    # Small region (< 10km2) to trigger _fetch_direct
    return CoordinateManager(lat_min=44.97, lat_max=44.98, lon_min=-93.27, lon_max=-93.26)

def test_ee_adapter_init(mock_credentials, mock_cache):
    # Mock ee.ServiceAccountCredentials and ee.Initialize
    with patch("ee.ServiceAccountCredentials") as mock_sa:
        with patch("ee.Initialize") as mock_init:
            adapter = EarthEngineAdapter(mock_credentials, mock_cache)
            assert adapter.credentials == mock_credentials
            # Should NOT be called on init (lazy loading)
            assert not mock_sa.called
            
            # Trigger initialization
            adapter._ensure_initialized()
            assert mock_sa.called
            assert mock_init.called

@pytest.mark.asyncio
async def test_ee_fetch_cache_hit(mock_credentials, mock_cache, coordinate_manager):
    with patch("ee.ServiceAccountCredentials"):
        with patch("ee.Initialize"):
            adapter = EarthEngineAdapter(mock_credentials, mock_cache)
            
            mock_cache.exists.return_value = True
            mock_cache.get_path.return_value = "/tmp/cached_ee.tif"
            
            result_path = await adapter.fetch(coordinate_manager, resolution=10, year=2023)
            
            assert result_path == "/tmp/cached_ee.tif"
            mock_cache.exists.assert_called_once()

@pytest.mark.asyncio
async def test_ee_fetch_logic_flow(mock_credentials, mock_cache, coordinate_manager):
    """Verifies that the fetch method calls the appropriate GEE API methods."""
    with patch("ee.ServiceAccountCredentials"):
        with patch("ee.Initialize"):
            adapter = EarthEngineAdapter(mock_credentials, mock_cache)
            
            mock_cache.exists.return_value = False
            
            # Mock the GEE collection and image logic
            with patch("ee.ImageCollection") as mock_coll_cls:
                with patch("ee.Geometry.Rectangle") as mock_rect_cls:
                    mock_image = MagicMock()
                    mock_collection = MagicMock()
                    
                    mock_coll_cls.return_value = mock_collection
                    mock_collection.filterDate.return_value = mock_collection
                    mock_collection.size.return_value.getInfo.return_value = 1
                    mock_collection.mosaic.return_value = mock_image
                    
                    mock_image.clip.return_value = mock_image
                    mock_image.reproject.return_value = mock_image
                    
                    # Mock the async fetch part (it's a small region in the test data)
                    with patch.object(adapter, "_fetch_direct", return_value="/tmp/exported.tif") as mock_fetch:
                        result = await adapter.fetch(coordinate_manager, resolution=10, year=2023)
                        
                        assert result == "/tmp/exported.tif"
                        assert mock_fetch.called