import os

class CacheManager:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _get_full_path(self, key, category, extension="tif"):
        category_dir = os.path.join(self.cache_dir, category)
        if not os.path.exists(category_dir):
            os.makedirs(category_dir)
        return os.path.join(category_dir, f"{key}.{extension}")

    def save(self, key, data, category, extension="tif"):
        """Saves binary data to the cache."""
        path = self._get_full_path(key, category, extension)
        with open(path, "wb") as f:
            f.write(data)
        return path

    def exists(self, key, category, extension="tif"):
        """Checks if a key exists in the cache."""
        path = self._get_full_path(key, category, extension)
        return os.path.exists(path)

    def get_path(self, key, category, extension="tif"):
        """Returns the path to a cached file, or None if it doesn't exist."""
        path = self._get_full_path(key, category, extension)
        if os.path.exists(path):
            return path
        return None
