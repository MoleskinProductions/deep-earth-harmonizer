import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from deep_earth.harmonize import Harmonizer
from deep_earth.coordinates import CoordinateManager
from deep_earth.providers.osm import OverpassAdapter

@pytest.fixture
def coordinate_manager():
    # Mock CM to return a fixed UTM bbox
    cm = MagicMock(spec=CoordinateManager)
    cm.get_utm_bbox.return_value = (0, 0, 100, 100)
    cm.utm_epsg = 32615
    cm.lat_min, cm.lat_max = 44.97, 44.99
    cm.lon_min, cm.lon_max = -93.28, -93.25
    return cm

def test_harmonizer_add_layers(coordinate_manager):
    """Test that the Harmonizer can store and manage additional data layers."""
    h = Harmonizer(coordinate_manager, resolution=10)
    
    # Dummy layers (e.g., from OSM provider)
    osm_layers = {
        "road_distance": np.ones((10, 10), dtype=np.float32),
        "building_mask": np.zeros((10, 10), dtype=np.uint8)
    }
    
    h.add_layers(osm_layers)
    
    assert hasattr(h, 'layers')
    assert "road_distance" in h.layers
    assert "building_mask" in h.layers
    assert h.layers["road_distance"].shape == (10, 10)
    assert np.all(h.layers["road_distance"] == 1)

def test_harmonizer_add_layers_validation(coordinate_manager):
    """Test that Harmonizer validates layer dimensions."""
    h = Harmonizer(coordinate_manager, resolution=10)
    
    # Wrong dimensions
    invalid_layers = {
        "bad_layer": np.ones((5, 5), dtype=np.float32)
    }
    
    with pytest.raises(ValueError, match="Layer dimensions"):
        h.add_layers(invalid_layers)

@pytest.mark.asyncio
async def test_harmonizer_osm_integration_flow(coordinate_manager):
    """Test the end-to-end integration flow between OverpassAdapter and Harmonizer."""
    # We use a real CoordinateManager for this one to ensure projection works
    from deep_earth.coordinates import CoordinateManager as RealCM
    cm = RealCM(lat_min=44.97, lat_max=44.99, lon_min=-93.28, lon_max=-93.25)
    
    h = Harmonizer(cm, resolution=10)
    adapter = OverpassAdapter()
    
    # Mock OSM data (WGS84)
    mock_elements = [
        {
            "type": "way", 
            "id": 1, 
            "tags": {"highway": "primary"}, 
            "geometry": [
                {"lat": 44.98, "lon": -93.26}, 
                {"lat": 44.985, "lon": -93.265}
            ]
        }
    ]
    
    # 1. Mock Fetch
    with patch.object(adapter, 'fetch', return_value={"elements": mock_elements}):
        data = await adapter.fetch((44.97, -93.28, 44.99, -93.25), 10)
        
        # 2. Parse Elements
        features = adapter._parse_elements(data["elements"])
        assert len(features) == 1
        
        # 3. Transform to grid (projects and rasterizes)
        layers = adapter.transform_to_grid(features, h)
        assert "road_distance" in layers
        
        # 4. Add to Harmonizer
        h.add_layers(layers)
        assert "road_distance" in h.layers
        assert h.layers["road_distance"].shape == (h.height, h.width)
        # Ensure some values were set (distance field shouldn't be all 1e6 if road exists)
        assert np.any(h.layers["road_distance"] < 1e6)