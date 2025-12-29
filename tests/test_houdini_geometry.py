import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from deep_earth.houdini.geometry import inject_heightfield

def test_inject_heightfield_calls_hou():
    # Mock the 'hou' module
    mock_hou = MagicMock()
    mock_hou.primitiveType.Volume = "Volume"
    mock_hou.attribType.Point = "Point"
    
    with patch.dict("sys.modules", {"hou": mock_hou}):
        geo = MagicMock()
        cm = MagicMock()
        h = MagicMock()
        h.width = 10
        h.height = 10
        
        height_grid = np.zeros((10, 10))
        embed_grid = np.zeros((64, 10, 10))
        
        inject_heightfield(geo, cm, h, height_grid, embed_grid)
        
        assert geo.addAttrib.called
        assert geo.setPointFloatAttribValues.called
