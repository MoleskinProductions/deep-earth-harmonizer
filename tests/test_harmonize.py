import pytest
import numpy as np
import rasterio
from deep_earth.harmonize import Harmonizer
from deep_earth.region import RegionContext as CoordinateManager

@pytest.fixture
def coordinate_manager():
    return CoordinateManager(lat_min=44.9, lat_max=45.1, lon_min=-93.1, lon_max=-92.9)

def test_harmonizer_init(coordinate_manager):
    h = Harmonizer(coordinate_manager, resolution=10)
    assert h.resolution == 10
    assert h.width > 0
    assert h.height > 0

def test_resample_to_master_grid(coordinate_manager, tmp_path):
    h = Harmonizer(coordinate_manager, resolution=10)
    
    # Create dummy source data (e.g., 30m DEM)
    src_path = tmp_path / "src.tif"
    src_data = np.random.rand(10, 10).astype(np.float32)
    with rasterio.open(
        src_path, 'w',
        driver='GTiff', height=10, width=10, count=1, dtype='float32',
        crs='EPSG:4326', transform=rasterio.transform.from_bounds(-93.1, 44.9, -92.9, 45.1, 10, 10)
    ) as dst:
        dst.write(src_data, 1)
        
    resampled = h.resample(str(src_path), bands=1)
    assert resampled.shape == (h.height, h.width)
    assert not np.all(resampled == 0)

def test_resample_multi_band(coordinate_manager, tmp_path):
    h = Harmonizer(coordinate_manager, resolution=10)
    
    # Create dummy 64-band source
    src_path = tmp_path / "multi.tif"
    src_data = np.random.rand(64, 10, 10).astype(np.float32)
    with rasterio.open(
        src_path, 'w',
        driver='GTiff', height=10, width=10, count=64, dtype='float32',
        crs='EPSG:4326', transform=rasterio.transform.from_bounds(-93.1, 44.9, -92.9, 45.1, 10, 10)
    ) as dst:
        dst.write(src_data)
        
    resampled = h.resample(str(src_path), bands=list(range(1, 65)))
    assert resampled.shape == (64, h.height, h.width)

def test_compute_quality_layer(coordinate_manager):
    h = Harmonizer(coordinate_manager, resolution=100)
    
    # DEM only
    q1 = h.compute_quality_layer(height_grid=np.zeros((h.height, h.width)))
    assert np.all(q1 == 0.25)
    
    # DEM + Embeddings
    q2 = h.compute_quality_layer(height_grid=np.zeros((h.height, h.width)), 
                                 embed_grid=np.zeros((64, h.height, h.width)))
    assert np.all(q2 == 0.75)
    
    # All
    h.add_layers({"highway": np.zeros((h.height, h.width))})
    q3 = h.compute_quality_layer(height_grid=np.zeros((h.height, h.width)), 
                                 embed_grid=np.zeros((64, h.height, h.width)))
    assert np.all(q3 == 1.0)
