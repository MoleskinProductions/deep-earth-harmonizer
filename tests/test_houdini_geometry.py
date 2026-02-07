import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from deep_earth.houdini.geometry import inject_heightfield

def test_inject_heightfield_calls_hou():
    # Mock the 'hou' module
    mock_hou = MagicMock()
    mock_hou.attribType.Point = "Point"

    with patch.dict("sys.modules", {"hou": mock_hou}):
        geo = MagicMock()
        cm = MagicMock()
        h = MagicMock()
        h.width = 10
        h.height = 10
        h.dst_transform = MagicMock()
        h.dst_transform.__mul__.return_value = (np.zeros((10, 10)), np.zeros((10, 10)))
        h.layers = {}

        height_grid = np.zeros((10, 10))
        embed_grid = np.zeros((64, 10, 10))

        inject_heightfield(geo, cm, h, height_grid, embed_grid)

        # Should clear geometry first
        geo.clear.assert_called_once()
        # Should create points
        assert geo.createPoints.called
        # Should add height attribute
        height_calls = [
            c for c in geo.addAttrib.call_args_list
            if c[0][1] == "height"
        ]
        assert len(height_calls) == 1
        # Should add embedding attribute
        assert geo.addAttrib.called
        assert geo.setPointFloatAttribValues.called
