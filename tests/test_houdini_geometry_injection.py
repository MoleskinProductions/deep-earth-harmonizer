import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from deep_earth.houdini.geometry import inject_heightfield
from deep_earth.coordinates import CoordinateManager
from deep_earth.harmonize import Harmonizer

def test_inject_heightfield_sets_positions():
    # Mock the 'hou' module
    mock_hou = MagicMock()
    mock_hou.primitiveType.Volume = "Volume"
    mock_hou.attribType.Point = "Point"
    
    with patch.dict("sys.modules", {"hou": mock_hou}):
        geo = MagicMock()
        # Mock primitives to return a height volume
        height_volume = MagicMock()
        height_volume.type.return_value = "Volume"
        height_volume.name.return_value = "height"
        geo.primitives.return_value = [height_volume]
        
        # Setup CoordinateManager and Harmonizer
        cm = CoordinateManager(45.0, 45.1, 10.0, 10.1)
        h = Harmonizer(cm, resolution=100)
        
        height_grid = np.zeros((h.height, h.width))
        embed_grid = np.zeros((64, h.height, h.width))
        
        inject_heightfield(geo, cm, h, height_grid, embed_grid)
        
        # Check if setPointFloatAttribValues was called for 'P'
        # We need to find the call where the first argument is "P"
        p_calls = [call for call in geo.setPointFloatAttribValues.call_args_list if call[0][0] == "P"]
        assert len(p_calls) == 1, "setPointFloatAttribValues('P', ...) was not called"
        
        # Verify positions
        positions = p_calls[0][0][1]
        assert len(positions) == h.width * h.height * 3
        
        # Check first point position (top-left cell center)
        expected_x, expected_y = h.dst_transform * (0.5, 0.5)
        expected_z = height_grid[0, 0]
        
        assert positions[0] == pytest.approx(expected_x)
        assert positions[1] == pytest.approx(expected_z) # In Houdini, Y is up, so height is Y
        assert positions[2] == pytest.approx(expected_y) # Z in Houdini is Y in UTM (North)
