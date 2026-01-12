import os
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union, cast

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Manages a local file-based cache for geospatial data.
    
    Metadata Version 2.0:
    - version: "2.0"
    - entries: {
        "key": {
            "category": str,
            "timestamp": str (ISO8601),
            "ttl_days": int,
            "extension": str
        }
    }
    """
    
    TTL_DAYS = {
        "srtm": None,      # Never expires
        "osm": 30,         # 30 days
        "embeddings": 365  # 1 year
    }

    def __init__(self, cache_dir: str):
        """
        Initialize the CacheManager.

        Args:
            cache_dir: Root directory for the cache.
        """
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        self.metadata_path = os.path.join(self.cache_dir, "cache_metadata.json")
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Loads and migrates cache metadata from disk."""
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                
                # Migration logic
                if self.metadata.get("version") == "1.0":
                    self._migrate_v1_to_v2()
                    
            except (json.JSONDecodeError, IOError):
                logger.error(f"Failed to load cache metadata from {self.metadata_path}. Initializing new metadata.")
                self.metadata = {"version": "2.0", "entries": {}}
        else:
            self.metadata = {"version": "2.0", "entries": {}}

    def _migrate_v1_to_v2(self) -> None:
        """Migrates metadata from version 1.0 to 2.0."""
        logger.info("Migrating cache metadata from v1.0 to v2.0")
        new_entries = {}
        for key, entry in self.metadata.get("entries", {}).items():
            created = entry.get("created", time.time())
            timestamp = datetime.fromtimestamp(created, tz=timezone.utc).isoformat()
            
            category = entry.get("category", "unknown")
            ttl_days = self.TTL_DAYS.get(category)
            
            new_entries[key] = {
                "category": category,
                "timestamp": timestamp,
                "ttl_days": ttl_days,
                "extension": entry.get("extension", "tif")
            }
        
        self.metadata = {
            "version": "2.0",
            "entries": new_entries
        }
        self._save_metadata()

    def _save_metadata(self) -> None:
        """Saves cache metadata to disk."""
        try:
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save cache metadata: {e}")

    def _get_full_path(self, key: str, category: str, extension: str = "tif") -> str:
        """Calculates the full filesystem path for a cache entry."""
        category_dir = os.path.join(self.cache_dir, category)
        if not os.path.exists(category_dir):
            os.makedirs(category_dir)
        return os.path.join(category_dir, f"{key}.{extension}")

    def _is_expired(self, key: str) -> bool:
        """Checks if a cache entry has exceeded its TTL."""
        if key not in self.metadata["entries"]:
            return False 
            
        entry = self.metadata["entries"][key]
        timestamp_str = entry.get("timestamp")
        ttl_days = entry.get("ttl_days")
        
        if timestamp_str is None or ttl_days is None:
            return False
            
        try:
            created = datetime.fromisoformat(timestamp_str)
            now = datetime.now(timezone.utc)
            age_days = (now - created).total_seconds() / (24 * 3600)
            return cast(bool, age_days > ttl_days)
        except (ValueError, TypeError):
            return True # Assume expired if timestamp is invalid

    def save(self, key: str, data: bytes, category: str, extension: str = "tif") -> str:
        """Saves binary data to the cache."""
        path = self._get_full_path(key, category, extension)
        try:
            with open(path, "wb") as f:
                f.write(data)
            
            self.metadata["entries"][key] = {
                "category": category,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ttl_days": self.TTL_DAYS.get(category),
                "extension": extension
            }
            self._save_metadata()
            return path
        except IOError as e:
            logger.error(f"Failed to save data to cache path {path}: {e}")
            raise

    def exists(self, key: str, category: str, extension: str = "tif") -> bool:
        """Checks if a key exists in the cache and is not expired."""
        if self._is_expired(key):
             self.invalidate(key)
             return False

        path = self._get_full_path(key, category, extension)
        return os.path.exists(path)

    def get_path(self, key: str, category: str, extension: str = "tif") -> Optional[str]:
        """Returns the path to a cached file if it exists and is not expired."""
        if self._is_expired(key):
             self.invalidate(key)
             return None

        path = self._get_full_path(key, category, extension)
        if os.path.exists(path):
            return path
        return None

    def invalidate(self, key: str) -> None:
        """Removes an entry from the cache."""
        if key in self.metadata["entries"]:
            entry = self.metadata["entries"][key]
            path = self._get_full_path(key, entry["category"], entry.get("extension", "tif"))
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError as e:
                    logger.error(f"Failed to remove cache file {path}: {e}")
            
            del self.metadata["entries"][key]
            self._save_metadata()
            
    def clear_expired(self) -> int:
        """Clears all expired entries from the cache."""
        keys = list(self.metadata["entries"].keys())
        cleared_count = 0
        for key in keys:
            if self._is_expired(key):
                self.invalidate(key)
                cleared_count += 1
        return cleared_count

