import os
import json
import time

class CacheManager:
    TTL_CONFIG = {
        "srtm": None, # Never
        "osm": 30 * 24 * 3600, # 30 days
        "embeddings": 365 * 24 * 3600 # 365 days
    }

    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        self.metadata_path = os.path.join(self.cache_dir, "cache_metadata.json")
        self._load_metadata()

    def _load_metadata(self):
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)
            except json.JSONDecodeError:
                self.metadata = {"version": "1.0", "entries": {}}
        else:
            self.metadata = {"version": "1.0", "entries": {}}

    def _save_metadata(self):
        with open(self.metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def _get_full_path(self, key, category, extension="tif"):
        category_dir = os.path.join(self.cache_dir, category)
        if not os.path.exists(category_dir):
            os.makedirs(category_dir)
        return os.path.join(category_dir, f"{key}.{extension}")

    def _is_expired(self, key):
        if key not in self.metadata["entries"]:
            return False 
            
        entry = self.metadata["entries"][key]
        category = entry.get("category")
        created = entry.get("created")
        
        ttl = self.TTL_CONFIG.get(category)
        if ttl is None:
            return False
            
        age = time.time() - created
        return age > ttl

    def save(self, key, data, category, extension="tif"):
        """Saves binary data to the cache."""
        path = self._get_full_path(key, category, extension)
        with open(path, "wb") as f:
            f.write(data)
        
        self.metadata["entries"][key] = {
            "category": category,
            "created": time.time(),
            "extension": extension
        }
        self._save_metadata()
        return path

    def exists(self, key, category, extension="tif"):
        """Checks if a key exists in the cache."""
        if self._is_expired(key):
             self.invalidate(key)
             return False

        path = self._get_full_path(key, category, extension)
        return os.path.exists(path)

    def get_path(self, key, category, extension="tif"):
        """Returns the path to a cached file, or None if it doesn't exist."""
        if self._is_expired(key):
             self.invalidate(key)
             return None

        path = self._get_full_path(key, category, extension)
        if os.path.exists(path):
            return path
        return None

    def invalidate(self, key):
        """Removes an entry from the cache."""
        if key in self.metadata["entries"]:
            entry = self.metadata["entries"][key]
            path = self._get_full_path(key, entry["category"], entry.get("extension", "tif"))
            if os.path.exists(path):
                os.remove(path)
            
            del self.metadata["entries"][key]
            self._save_metadata()

