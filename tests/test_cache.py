import os
import pytest
import shutil
from deep_earth.cache import CacheManager

@pytest.fixture
def temp_cache_dir(tmp_path):
    cache_dir = tmp_path / "deep_earth_cache"
    return str(cache_dir)

def test_cache_save_retrieve(temp_cache_dir):
    manager = CacheManager(temp_cache_dir)
    key = "test_key"
    data = b"some binary data"
    
    # Save
    path = manager.save(key, data, category="srtm")
    assert os.path.exists(path)
    assert "srtm" in path
    
    # Exists
    assert manager.exists(key, category="srtm")
    
    # Get path
    assert manager.get_path(key, category="srtm") == path
    
    # Retrieve
    with open(path, "rb") as f:
        assert f.read() == data

def test_cache_missing(temp_cache_dir):
    manager = CacheManager(temp_cache_dir)
    assert not manager.exists("missing_key", category="srtm")
    assert manager.get_path("missing_key", category="srtm") is None