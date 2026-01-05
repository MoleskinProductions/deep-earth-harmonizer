import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import aiohttp
from deep_earth.providers.osm import OverpassAdapter
from deep_earth.providers.base import DataProviderAdapter
import json
import hashlib
from shapely.geometry import LineString, Polygon, Point
import numpy as np

def test_overpass_adapter_initialization():
    """Test that OverpassAdapter initializes correctly and inherits from DataProviderAdapter."""
    adapter = OverpassAdapter()
    assert isinstance(adapter, DataProviderAdapter)
    assert adapter.base_url == "https://overpass-api.de/api/interpreter"

def test_overpass_adapter_custom_url():
    """Test initializing with a custom Overpass API URL."""
    custom_url = "https://lz4.overpass-api.de/api/interpreter"
    adapter = OverpassAdapter(base_url=custom_url)
    assert adapter.base_url == custom_url

def test_build_query():
    """Test generating an Overpass QL query."""
    adapter = OverpassAdapter()
    bbox = (44.97, -93.28, 44.99, -93.25)
    query = adapter._build_query(bbox)
    assert "[out:json]" in query
    assert "[timeout:25]" in query
    bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
    assert bbox_str in query

    features = [
        'way["highway"]',
        'way["waterway"]',
        'way["building"]',
        'way["landuse"]',
        'way["natural"]',
        'relation["building"]',
        'relation["landuse"]',
        'relation["natural"]'
    ]
    for feature in features:
        assert feature in query

def test_endpoint_fallback_config():
    """Test configuring the adapter with fallback URLs."""
    fallbacks = [
        "https://lz4.overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]
    adapter = OverpassAdapter(fallback_urls=fallbacks)
    assert adapter.fallback_urls == fallbacks

@pytest.mark.asyncio
async def test_fetch_success():
    """Test successful async data fetching."""
    adapter = OverpassAdapter()
    # Mock cache to avoid filesystem usage
    adapter.cache = MagicMock()
    adapter.cache.exists.return_value = False
    
    bbox = (44.97, -93.28, 44.99, -93.25)
    resolution = 10.0
    
    mock_response_data = {"elements": [{"type": "way", "id": 1}]}
    mock_response_bytes = json.dumps(mock_response_data).encode('utf-8')
    
    with patch("aiohttp.ClientSession") as MockSession:
        mock_session_instance = MockSession.return_value
        mock_session_instance.__aenter__.return_value = mock_session_instance

        mock_get_ctx = MagicMock()
        mock_session_instance.get.return_value = mock_get_ctx
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = mock_response_data
        mock_response.read.return_value = mock_response_bytes
        
        mock_get_ctx.__aenter__.return_value = mock_response
        
        result = await adapter.fetch(bbox, resolution)
        
        assert result == mock_response_data

def test_get_cache_key():
    """Test generating a unique cache key."""
    adapter = OverpassAdapter()
    bbox = (44.97, -93.28, 44.99, -93.25)
    resolution = 10.0
    key = adapter.get_cache_key(bbox, resolution)
    assert isinstance(key, str)
    # Check it's a valid hex digest
    assert len(key) == 32 
    
    bbox2 = (45.0, -93.0, 45.1, -92.9)
    key2 = adapter.get_cache_key(bbox2, resolution)
    assert key != key2

@pytest.mark.asyncio
async def test_fetch_caching():
    """Test that fetched data is cached."""
    adapter = OverpassAdapter()
    # Mock cache directly on the instance
    adapter.cache = MagicMock()
    adapter.cache.exists.return_value = False
    
    bbox = (44.97, -93.28, 44.99, -93.25)
    resolution = 10.0
    mock_response_data = {"elements": []}
    mock_response_bytes = json.dumps(mock_response_data).encode('utf-8')

    with patch("aiohttp.ClientSession") as MockSession:
        mock_session_instance = MockSession.return_value
        mock_session_instance.__aenter__.return_value = mock_session_instance
        mock_get_ctx = MagicMock()
        mock_session_instance.get.return_value = mock_get_ctx
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = mock_response_data
        mock_response.read.return_value = mock_response_bytes
        
        mock_get_ctx.__aenter__.return_value = mock_response
        
        await adapter.fetch(bbox, resolution)
        
        # Verify save was called
        assert adapter.cache.save.called
        args = adapter.cache.save.call_args
        assert args[0][1] == mock_response_bytes
        assert args[0][2] == "osm"
        assert args[0][3] == "json"

def test_parse_elements():
    """Test parsing Overpass JSON elements into Shapely geometries."""
    adapter = OverpassAdapter()
    
    # Mock data with ways containing geometry (assuming 'out geom' was used)
    mock_data = {
        "elements": [
            {
                "type": "way",
                "id": 1,
                "tags": {"highway": "residential"},
                "geometry": [
                    {"lat": 45.0, "lon": -93.0},
                    {"lat": 45.1, "lon": -93.1}
                ]
            },
            {
                "type": "way",
                "id": 2,
                "tags": {"building": "yes", "height": "10"},
                "geometry": [
                    {"lat": 45.0, "lon": -93.0},
                    {"lat": 45.01, "lon": -93.0},
                    {"lat": 45.01, "lon": -93.01},
                    {"lat": 45.0, "lon": -93.0}
                ]
            }
        ]
    }
    
    features = adapter._parse_elements(mock_data["elements"])
    
    assert len(features) == 2
    # Check first feature (Road)
    assert features[0]["type"] == "road"
    assert isinstance(features[0]["geometry"], LineString)
    
    # Check second feature (Building)
    assert features[1]["type"] == "building"
    assert isinstance(features[1]["geometry"], Polygon)
    assert features[1]["tags"]["height"] == 10.0

def test_transform_to_grid():
    """Test rasterizing features into a grid."""
    adapter = OverpassAdapter()
    grid = MagicMock()
    grid.width = 10
    grid.height = 10
    # simplified transform for test
    grid.dst_transform = [1.0, 0, 0, 0, -1.0, 10]
    grid.dst_crs = "EPSG:3857"
    
    # Mock data from _parse_elements (using small coords for simple grid)
    data = [
        {
            "type": "road",
            "geometry": LineString([(1, 1), (9, 9)]),
            "tags": {"highway": "primary"}
        },
        {
            "type": "building",
            "geometry": Polygon([(2, 2), (2, 4), (4, 4), (4, 2), (2, 2)]),
            "tags": {"building": "yes", "height": 15.0}
        }
    ]
    
    # Mock projection to avoid actual pyproj call during unit test if possible
    with patch("deep_earth.providers.osm.pyproj.Transformer.from_crs") as MockTransformer:
        # Mock transformer to return input as is (identity)
        mock_trans = MockTransformer.return_value
        mock_trans.transform.side_effect = lambda x, y: (x, y)
        
        result = adapter.transform_to_grid(data, grid)
        
        assert "road_distance" in result
        assert "building_mask" in result
        assert "building_height" in result
        assert isinstance(result["road_distance"], np.ndarray)
        assert result["road_distance"].shape == (10, 10)
        assert result["building_mask"].shape == (10, 10)
        
        # Verify road distance field has values > 0
        assert np.any(result["road_distance"] > 0)
        # Verify building mask has 1s
        assert np.any(result["building_mask"] == 1)
