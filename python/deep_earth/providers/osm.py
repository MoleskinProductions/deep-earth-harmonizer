import hashlib
import json
import aiohttp
from typing import Any
from deep_earth.providers.base import DataProviderAdapter
from deep_earth.cache import CacheManager
from deep_earth.config import Config

class OverpassAdapter(DataProviderAdapter):
    """
    Adapter for fetching and processing OpenStreetMap data via the Overpass API.
    """
    DEFAULT_API_URL = "https://overpass-api.de/api/interpreter"

    def __init__(self, base_url: str = None, fallback_urls: list[str] = None, cache_dir: str = None):
        """
        Initialize the OverpassAdapter.

        Args:
            base_url (str, optional): The base URL for the Overpass API. 
                                      Defaults to the main public instance.
            fallback_urls (list[str], optional): List of fallback API URLs.
            cache_dir (str, optional): Custom cache directory.
        """
        self.base_url = base_url or self.DEFAULT_API_URL
        self.fallback_urls = fallback_urls or []
        
        if cache_dir is None:
            config = Config()
            cache_dir = config.cache_path
        self.cache = CacheManager(cache_dir)

    def _build_query(self, bbox: tuple[float, float, float, float]) -> str:
        """
        Construct an Overpass QL query for the given bounding box.
        
        Args:
            bbox: Tuple of (min_lat, min_lon, max_lat, max_lon)
            
        Returns:
            str: The formatted Overpass QL query string.
        """
        min_lat, min_lon, max_lat, max_lon = bbox
        bbox_str = f"{min_lat},{min_lon},{max_lat},{max_lon}"
        
        query = f"""
        [out:json][timeout:25];
        (
          way["highway"]({bbox_str});
          way["waterway"]({bbox_str});
          way["building"]({bbox_str});
          relation["building"]({bbox_str});
          way["landuse"]({bbox_str});
          relation["landuse"]({bbox_str});
          way["natural"]({bbox_str});
          relation["natural"]({bbox_str});
        );
        out body;
        >;
        out skel qt;
        """
        return query.strip()

    def get_cache_key(self, bbox: Any, resolution: float) -> str:
        """Generates a unique cache key for the given parameters."""
        # OSM fetch depends only on bbox, resolution is for rasterization later.
        bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
        return hashlib.md5(bbox_str.encode()).hexdigest()

    async def fetch(self, bbox: Any, resolution: float) -> Any:
        """
        Fetch data from Overpass API.
        
        Args:
            bbox: Tuple of (min_lat, min_lon, max_lat, max_lon)
            resolution: Not used for Overpass fetch, but required by interface.
            
        Returns:
            dict: The JSON response from Overpass.
        """
        key = self.get_cache_key(bbox, resolution)
        
        # Check cache
        if self.cache.exists(key, "osm", "json"):
            path = self.cache.get_path(key, "osm", "json")
            with open(path, "r") as f:
                return json.load(f)

        query = self._build_query(bbox)
        
        async with aiohttp.ClientSession() as session:
            # Overpass API takes the query in the 'data' parameter
            async with session.get(self.base_url, params={'data': query}) as response:
                if response.status == 200:
                    data = await response.read()
                    self.cache.save(key, data, "osm", "json")
                    return json.loads(data)
                else:
                    # In a real scenario we would try fallbacks here
                    response.raise_for_status()

    def validate_credentials(self) -> bool:
        # Overpass API (public) typically doesn't require credentials
        return True

    def transform_to_grid(self, data: Any, target_grid: Any) -> Any:
        pass
