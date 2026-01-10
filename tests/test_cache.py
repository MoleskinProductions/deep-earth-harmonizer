import os
import pytest
import shutil
import json
import time
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

def test_cache_metadata_creation(temp_cache_dir):
    manager = CacheManager(temp_cache_dir)
    key = "meta_test"
    data = b"data"
    
    manager.save(key, data, category="srtm")
    
    meta_path = os.path.join(temp_cache_dir, "cache_metadata.json")
    assert os.path.exists(meta_path)
    
    with open(meta_path, 'r') as f:
        meta = json.load(f)
        assert "entries" in meta
        assert key in meta["entries"]
        assert meta["entries"][key]["category"] == "srtm"
        assert "created" in meta["entries"][key]

def test_cache_ttl_expiration(temp_cache_dir):
    manager = CacheManager(temp_cache_dir)
    manager.TTL_CONFIG = {"short_lived": 0.1} # 0.1 seconds
    
    key = "ttl_test"
    data = b"data"
    manager.save(key, data, category="short_lived")
    
    assert manager.exists(key, category="short_lived")
    
    time.sleep(0.2)
    # Should be expired
    assert not manager.exists(key, category="short_lived")

def test_cache_invalidation(temp_cache_dir):
    manager = CacheManager(temp_cache_dir)
    key = "inv_test"
    manager.save(key, b"data", category="srtm")
    
    assert manager.exists(key, category="srtm")
    manager.invalidate(key)
    assert not manager.exists(key, category="srtm")

def test_cache_metadata_corruption(temp_cache_dir):
    os.makedirs(temp_cache_dir, exist_ok=True)
    meta_path = os.path.join(temp_cache_dir, "cache_metadata.json")
    with open(meta_path, 'w') as f:
        f.write("{invalid_json")
        
    manager = CacheManager(temp_cache_dir)
    assert manager.metadata["entries"] == {}
