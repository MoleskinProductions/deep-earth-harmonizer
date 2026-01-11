import os
import json
import time
import logging
from typing import Dict, Any, Optional, Union, cast

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Manages a local file-based cache for geospatial data.
    
    Attributes:
        cache_dir (str): Root directory for the cache.
        metadata_path (str): Path to the JSON metadata file.
        metadata (Dict[str, Any]): Dictionary containing cache entry information.
    """
    
    TTL_CONFIG = {
        "srtm": None, # Never
        "osm": 30 * 24 * 3600, # 30 days
        "embeddings": 365 * 24 * 3600 # 365 days
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
        """Loads cache metadata from disk."""
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)
            except (json.JSONDecodeError, IOError):
                logger.error(f"Failed to load cache metadata from {self.metadata_path}. Initializing new metadata.")
                self.metadata = {"version": "1.0", "entries": {}}
        else:
            self.metadata = {"version": "1.0", "entries": {}}

    def _save_metadata(self) -> None:
        """Saves cache metadata to disk."""
        try:
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save cache metadata: {e}")

    def _get_full_path(self, key: str, category: str, extension: str = "tif") -> str:
        """
        Calculates the full filesystem path for a cache entry.

        Args:
            key: Unique key for the entry.
            category: Data category (e.g., 'srtm', 'osm').
            extension: File extension.

        Returns:
            The full path to the file.
        """
        category_dir = os.path.join(self.cache_dir, category)
        if not os.path.exists(category_dir):
            os.makedirs(category_dir)
        return os.path.join(category_dir, f"{key}.{extension}")

    def _is_expired(self, key: str) -> bool:
        """
        Checks if a cache entry has exceeded its TTL.

        Args:
            key: Unique key for the entry.

        Returns:
            True if expired, False otherwise.
        """
        if key not in self.metadata["entries"]:
            return False 
            
        entry = self.metadata["entries"][key]
        category = entry.get("category")
        created = entry.get("created")
        
        ttl = self.TTL_CONFIG.get(category)
        if ttl is None or created is None:
            return False
            
        age = time.time() - created
        return cast(bool, age > ttl)

    def save(self, key: str, data: bytes, category: str, extension: str = "tif") -> str:
        """
        Saves binary data to the cache.

        Args:
            key: Unique key for the entry.
            data: Binary data to save.
            category: Data category.
            extension: File extension.

        Returns:
            The path to the saved file.
        """
        path = self._get_full_path(key, category, extension)
        try:
            with open(path, "wb") as f:
                f.write(data)
            
            self.metadata["entries"][key] = {
                "category": category,
                "created": time.time(),
                "extension": extension
            }
            self._save_metadata()
            return path
        except IOError as e:
            logger.error(f"Failed to save data to cache path {path}: {e}")
            raise

    def exists(self, key: str, category: str, extension: str = "tif") -> bool:
        """
        Checks if a key exists in the cache and is not expired.

        Args:
            key: Unique key for the entry.
            category: Data category.
            extension: File extension.

        Returns:
            True if it exists and is valid, False otherwise.
        """
        if self._is_expired(key):
             self.invalidate(key)
             return False

        path = self._get_full_path(key, category, extension)
        return os.path.exists(path)

    def get_path(self, key: str, category: str, extension: str = "tif") -> Optional[str]:
        """
        Returns the path to a cached file if it exists and is not expired.

        Args:
            key: Unique key for the entry.
            category: Data category.
            extension: File extension.

        Returns:
            The path to the file, or None if it doesn't exist or is expired.
        """
        if self._is_expired(key):
             self.invalidate(key)
             return None

        path = self._get_full_path(key, category, extension)
        if os.path.exists(path):
            return path
        return None

    def invalidate(self, key: str) -> None:
        """
        Removes an entry from the cache.

        Args:
            key: Unique key for the entry.
        """
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

