import pytest
from deep_earth.providers.osm import OverpassAdapter
from deep_earth.providers.base import DataProviderAdapter

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
    # bbox: (min_lat, min_lon, max_lat, max_lon)
    bbox = (44.97, -93.28, 44.99, -93.25)
    
    query = adapter._build_query(bbox)
    
    # Check for basic headers
    assert "[out:json]" in query
    assert "[timeout:25]" in query
    
    # Check for bbox string injection
    # Overpass bbox: (south, west, north, east)
    bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
    assert bbox_str in query

    # Check for required feature types
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