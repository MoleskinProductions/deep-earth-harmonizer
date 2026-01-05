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
