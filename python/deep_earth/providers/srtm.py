import aiohttp
import numpy as np
import rasterio
from io import BytesIO
from .base import DataProviderAdapter

class SRTMAdapter(DataProviderAdapter):
    def __init__(self, credentials, cache):
        self.credentials = credentials
        self.cache = cache
        self.api_url = "https://portal.opentopography.org/API/globaldem"

    def get_cache_key(self, bbox, resolution):
        return f"srtm_{bbox.lat_min}_{bbox.lat_max}_{bbox.lon_min}_{bbox.lon_max}_{resolution}"

    def validate_credentials(self):
        return self.credentials.get_opentopography_key() is not None

    async def fetch(self, bbox, resolution):
        """Fetches SRTM data from OpenTopography and returns the path to the cached file."""
        cache_key = self.get_cache_key(bbox, resolution)
        
        if self.cache.exists(cache_key, category="srtm"):
            return self.cache.get_path(cache_key, category="srtm")

        params = {
            "demtype": "SRTMGL1" if resolution <= 30 else "SRTMGL3",
            "south": bbox.lat_min,
            "north": bbox.lat_max,
            "west": bbox.lon_min,
            "east": bbox.lon_max,
            "outputFormat": "GTiff",
            "API_Key": self.credentials.get_opentopography_key()
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_url, params=params) as response:
                if response.status == 200:
                    data = await response.read()
                    return self.cache.save(cache_key, data, category="srtm")
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to fetch SRTM: {response.status} - {error_text}")

    def transform_to_grid(self, data_path, target_grid):
        """Loads the GeoTIFF and resamples it to the target grid."""
        with rasterio.open(data_path) as src:
            # Basic implementation for now: read first band
            # In Phase 5 we will add sophisticated harmonization
            return src.read(1)
