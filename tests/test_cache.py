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


def test_cache_save_metadata_io_error(temp_cache_dir):
    """IOError during metadata save is logged, not raised."""
    manager = CacheManager(temp_cache_dir)
    manager.save("k1", b"data", category="srtm")
    # Make metadata path read-only to trigger IOError
    os.chmod(manager.metadata_path, 0o444)
    try:
        # _save_metadata should catch the IOError
        manager._save_metadata()
    finally:
        os.chmod(manager.metadata_path, 0o644)


def test_cache_is_expired_invalid_timestamp(temp_cache_dir):
    """Invalid ISO timestamp -> treated as expired."""
    manager = CacheManager(temp_cache_dir)
    manager.metadata["entries"]["bad_ts"] = {
        "category": "osm",
        "timestamp": "not-a-date",
        "ttl_days": 30,
        "extension": "json",
    }
    assert manager._is_expired("bad_ts") is True


def test_cache_save_io_error(temp_cache_dir):
    """IOError during data write propagates."""
    manager = CacheManager(temp_cache_dir)
    # Create category dir then make it read-only
    cat_dir = os.path.join(temp_cache_dir, "srtm")
    os.makedirs(cat_dir, exist_ok=True)
    os.chmod(cat_dir, 0o444)
    try:
        with pytest.raises(IOError):
            manager.save("fail_key", b"data", category="srtm")
    finally:
        os.chmod(cat_dir, 0o755)


def test_cache_exists_expired_invalidates(temp_cache_dir):
    """exists() on an expired key invalidates it and returns False."""
    manager = CacheManager(temp_cache_dir)
    manager.save("exp", b"data", category="osm")
    expired_ts = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    manager.metadata["entries"]["exp"]["timestamp"] = expired_ts
    manager._save_metadata()

    assert manager.exists("exp", category="osm") is False
    assert "exp" not in manager.metadata["entries"]


def test_cache_get_path_expired_returns_none(temp_cache_dir):
    """get_path() on an expired key returns None and invalidates."""
    manager = CacheManager(temp_cache_dir)
    manager.save("gp", b"data", category="osm")
    expired_ts = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    manager.metadata["entries"]["gp"]["timestamp"] = expired_ts
    manager._save_metadata()

    assert manager.get_path("gp", category="osm") is None
    assert "gp" not in manager.metadata["entries"]


def test_cache_invalidate_os_error(temp_cache_dir):
    """OSError during file removal is logged, entry still removed."""
    manager = CacheManager(temp_cache_dir)
    path = manager.save("rm_fail", b"data", category="srtm")
    # Make file read-only and dir non-writable to trigger OSError
    os.chmod(path, 0o444)
    cat_dir = os.path.dirname(path)
    os.chmod(cat_dir, 0o555)
    try:
        manager.invalidate("rm_fail")
    finally:
        os.chmod(cat_dir, 0o755)
    # Entry should be removed from metadata even though file delete failed
    assert "rm_fail" not in manager.metadata["entries"]


def test_cache_clear_expired(temp_cache_dir):
    """clear_expired removes only expired entries."""
    manager = CacheManager(temp_cache_dir)
    # Save two entries
    manager.save("fresh", b"data", category="osm")
    manager.save("stale", b"data", category="osm")

    # Make one expired
    expired_ts = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    manager.metadata["entries"]["stale"]["timestamp"] = expired_ts
    manager._save_metadata()

    cleared = manager.clear_expired()
    assert cleared == 1
    assert "fresh" in manager.metadata["entries"]
    assert "stale" not in manager.metadata["entries"]