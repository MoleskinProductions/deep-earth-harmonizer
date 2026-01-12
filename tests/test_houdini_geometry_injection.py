import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from deep_earth.houdini.geometry import inject_heightfield
from deep_earth.region import RegionContext as CoordinateManager
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
        
        # Check if createPoints was called with the correct number of points
        create_points_calls = geo.createPoints.call_args_list
        assert len(create_points_calls) == 1
        
        # Verify positions
        positions = create_points_calls[0][0][0]
        assert len(positions) == h.width * h.height
        assert len(positions[0]) == 3
        
        # Check first point position (top-left cell center)
        expected_x, expected_y = h.dst_transform * (0.5, 0.5)
        expected_z = height_grid[0, 0]
        
        assert positions[0][0] == pytest.approx(expected_x)
        assert positions[0][1] == pytest.approx(expected_z) # In Houdini, Y is up, so height is Y
        assert positions[0][2] == pytest.approx(expected_y) # Z in Houdini is Y in UTM (North)
        
def test_inject_heightfield_injects_osm_attributes():
    # Mock the 'hou' module
    mock_hou = MagicMock()
    mock_hou.primitiveType.Volume = "Volume"
    mock_hou.attribType.Point = "Point"
    
    with patch.dict("sys.modules", {"hou": mock_hou}):
        geo = MagicMock()
        height_volume = MagicMock()
        height_volume.type.return_value = "Volume"
        height_volume.name.return_value = "height"
        geo.primitives.return_value = [height_volume]
        
        cm = CoordinateManager(45.0, 45.1, 10.0, 10.1)
        h = Harmonizer(cm, resolution=100)
        
        # Add OSM layers to harmonizer
        road_dist = np.random.rand(h.height, h.width).astype(np.float32)
        landuse_id = np.random.randint(0, 10, (h.height, h.width)).astype(np.int32)
        h.add_layers({
            "road_distance": road_dist,
            "landuse_id": landuse_id
        })
        
        height_grid = np.zeros((h.height, h.width))
        embed_grid = np.zeros((64, h.height, h.width))
        
        inject_heightfield(geo, cm, h, height_grid, embed_grid)
        
        # Check if attributes were added
        # geo.addAttrib(hou.attribType.Point, name, default_value)
        add_attrib_calls = [call[0][1] for call in geo.addAttrib.call_args_list]
        assert "road_distance" in add_attrib_calls
        assert "landuse_id" in add_attrib_calls
        
        # Check if values were set
        # geo.setPointFloatAttribValues(name, values) or geo.setPointIntAttribValues(name, values)
        # For road_distance (float)
        road_dist_calls = [call for call in geo.setPointFloatAttribValues.call_args_list if call[0][0] == "road_distance"]
        assert len(road_dist_calls) == 1
        
        # For landuse_id (int)
        landuse_id_calls = [call for call in geo.setPointIntAttribValues.call_args_list if call[0][0] == "landuse_id"]
        assert len(landuse_id_calls) == 1

def test_inject_heightfield_injects_string_attributes():
    # Mock the 'hou' module
    mock_hou = MagicMock()
    mock_hou.primitiveType.Volume = "Volume"
    mock_hou.attribType.Point = "Point"
    
    with patch.dict("sys.modules", {"hou": mock_hou}):
        geo = MagicMock()
        height_volume = MagicMock()
        height_volume.type.return_value = "Volume"
        height_volume.name.return_value = "height"
        geo.primitives.return_value = [height_volume]
        
        cm = CoordinateManager(45.0, 45.1, 10.0, 10.1)
        h = Harmonizer(cm, resolution=100)
        
        # Add a string layer
        highway = np.full((h.height, h.width), "primary", dtype=object)
        h.add_layers({"highway": highway})
        
        height_grid = np.zeros((h.height, h.width))
        embed_grid = np.zeros((64, h.height, h.width))
        
        inject_heightfield(geo, cm, h, height_grid, embed_grid)
        
        # Check if attribute was added
        add_attrib_calls = [call[0][1] for call in geo.addAttrib.call_args_list]
        assert "highway" in add_attrib_calls
        
        # Check if values were set using setPointStringAttribValues
        highway_calls = [call for call in geo.setPointStringAttribValues.call_args_list if call[0][0] == "highway"]
        assert len(highway_calls) == 1
        assert highway_calls[0][0][1][0] == "primary"

def test_inject_heightfield_viz_pca():
    mock_hou = MagicMock()
    mock_hou.primitiveType.Volume = "Volume"
    mock_hou.attribType.Point = "Point"
    
    with patch.dict("sys.modules", {"hou": mock_hou}):
        geo = MagicMock()
        height_volume = MagicMock()
        height_volume.type.return_value = "Volume"
        height_volume.name.return_value = "height"
        geo.primitives.return_value = [height_volume]
        
        cm = CoordinateManager(45.0, 45.1, 10.0, 10.1)
        h = Harmonizer(cm, resolution=100)
        
        height_grid = np.zeros((h.height, h.width))
        # Embeddings with some variance
        embed_grid = np.random.rand(64, h.height, h.width)
        
        inject_heightfield(geo, cm, h, height_grid, embed_grid, viz_mode="pca")
        
        # Check if Cd was added
        add_attrib_calls = [call[0][1] for call in geo.addAttrib.call_args_list]
        assert "Cd" in add_attrib_calls
        
        # Check if Cd values were set
        cd_calls = [call for call in geo.setPointFloatAttribValues.call_args_list if call[0][0] == "Cd"]
        assert len(cd_calls) == 1

def test_inject_heightfield_viz_biome():
    mock_hou = MagicMock()
    mock_hou.primitiveType.Volume = "Volume"
    mock_hou.attribType.Point = "Point"
    
    with patch.dict("sys.modules", {"hou": mock_hou}):
        geo = MagicMock()
        height_volume = MagicMock()
        height_volume.type.return_value = "Volume"
        height_volume.name.return_value = "height"
        geo.primitives.return_value = [height_volume]
        
        cm = CoordinateManager(45.0, 45.1, 10.0, 10.1)
        h = Harmonizer(cm, resolution=100)
        h.add_layers({"landuse": np.full((h.height, h.width), "forest", dtype=object)})
        
        height_grid = np.zeros((h.height, h.width))
        embed_grid = np.zeros((64, h.height, h.width))
        
        inject_heightfield(geo, cm, h, height_grid, embed_grid, viz_mode="biome")
        
        # Check if Cd was added
        add_attrib_calls = [call[0][1] for call in geo.addAttrib.call_args_list]
        assert "Cd" in add_attrib_calls
        
        # Check if Cd values were set
        cd_calls = [call for call in geo.setPointFloatAttribValues.call_args_list if call[0][0] == "Cd"]
        assert len(cd_calls) == 1
        # Check if it's green (forest)
        cd_values = cd_calls[0][0][1]
        assert cd_values[0] == pytest.approx(0.1)
        assert cd_values[1] == pytest.approx(0.5)
        assert cd_values[2] == pytest.approx(0.1)

def test_inject_heightfield_data_quality():
    mock_hou = MagicMock()
    mock_hou.primitiveType.Volume = "Volume"
    mock_hou.attribType.Point = "Point"
    
    with patch.dict("sys.modules", {"hou": mock_hou}):
        geo = MagicMock()
        height_volume = MagicMock()
        height_volume.type.return_value = "Volume"
        height_volume.name.return_value = "height"
        geo.primitives.return_value = [height_volume]
        
        cm = CoordinateManager(45.0, 45.1, 10.0, 10.1)
        h = Harmonizer(cm, resolution=100)
        
        height_grid = np.zeros((h.height, h.width))
        embed_grid = np.zeros((64, h.height, h.width))
        
        # Compute and add quality layer
        quality = h.compute_quality_layer(height_grid, embed_grid)
        h.add_layers({"data_quality": quality})
        
        inject_heightfield(geo, cm, h, height_grid, embed_grid)
        
        # Check if data_quality attribute was added
        add_attrib_calls = [call[0][1] for call in geo.addAttrib.call_args_list]
        assert "data_quality" in add_attrib_calls
        
        # Check if values were set (DEM + Embeddings = 0.75)
        dq_calls = [call for call in geo.setPointFloatAttribValues.call_args_list if call[0][0] == "data_quality"]
        assert len(dq_calls) == 1
        assert dq_calls[0][0][1][0] == pytest.approx(0.75)
