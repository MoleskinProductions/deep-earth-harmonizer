import os
import pytest
import shutil
import json
import time
from datetime import datetime, timezone, timedelta
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
        assert meta["version"] == "2.0"
        assert "entries" in meta
        assert key in meta["entries"]
        assert meta["entries"][key]["category"] == "srtm"
        assert "timestamp" in meta["entries"][key]
        assert "ttl_days" in meta["entries"][key]

def test_cache_ttl_expiration(temp_cache_dir):
    manager = CacheManager(temp_cache_dir)
    # Manually set an expired timestamp in metadata
    key = "ttl_test"
    manager.save(key, b"data", category="osm")
    
    # 31 days ago
    expired_ts = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
    manager.metadata["entries"][key]["timestamp"] = expired_ts
    manager._save_metadata()
    
    # Should be expired
    assert not manager.exists(key, category="osm")

def test_cache_invalidation(temp_cache_dir):
    manager = CacheManager(temp_cache_dir)
    key = "inv_test"
    manager.save(key, b"data", category="srtm")
    
    assert manager.exists(key, category="srtm")
    manager.invalidate(key)
    assert not manager.exists(key, category="srtm")

def test_cache_migration_v1_to_v2(temp_cache_dir):
    # Create v1.0 metadata
    os.makedirs(temp_cache_dir, exist_ok=True)
    meta_path = os.path.join(temp_cache_dir, "cache_metadata.json")
    created_time = time.time() - 3600 # 1 hour ago
    v1_meta = {
        "version": "1.0",
        "entries": {
            "old_entry": {
                "category": "srtm",
                "created": created_time,
                "extension": "tif"
            }
        }
    }
    with open(meta_path, 'w') as f:
        json.dump(v1_meta, f)
        
    # Instantiate manager
    manager = CacheManager(temp_cache_dir)
    
    # Check if migrated
    assert manager.metadata["version"] == "2.0"
    assert "old_entry" in manager.metadata["entries"]
    entry = manager.metadata["entries"]["old_entry"]
    assert "timestamp" in entry
    assert entry["category"] == "srtm"
    assert entry["ttl_days"] is None
    
    # Verify timestamp conversion
    dt = datetime.fromisoformat(entry["timestamp"])
    assert abs(dt.timestamp() - created_time) < 1.0

def test_cache_metadata_corruption(temp_cache_dir):
    os.makedirs(temp_cache_dir, exist_ok=True)
    meta_path = os.path.join(temp_cache_dir, "cache_metadata.json")
    with open(meta_path, 'w') as f:
        f.write("{invalid_json")
        
    manager = CacheManager(temp_cache_dir)
    assert manager.metadata["entries"] == {}