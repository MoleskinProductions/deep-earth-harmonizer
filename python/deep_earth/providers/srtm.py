import logging
import aiohttp
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling

from deep_earth.bbox import BoundingBox
from .base import DataProviderAdapter

logger = logging.getLogger(__name__)


class SRTMAdapter(DataProviderAdapter):
    def __init__(self, credentials, cache):
        self.credentials = credentials
        self.cache = cache
        self.api_url = "https://portal.opentopography.org/API/globaldem"

    def get_cache_key(self, bbox: BoundingBox, resolution: float) -> str:
        return f"srtm_{bbox.lat_min}_{bbox.lat_max}_{bbox.lon_min}_{bbox.lon_max}_{resolution}"

    def validate_credentials(self) -> bool:
        return self.credentials.get_opentopography_key() is not None

    async def fetch(self, bbox: BoundingBox, resolution: float) -> str:
        """Fetches SRTM data from OpenTopography and returns the path to the cached file."""
        logger.info(f"Fetching SRTM for bbox {bbox} at resolution {resolution}")
        cache_key = self.get_cache_key(bbox, resolution)
        
        if self.cache.exists(cache_key, category="srtm"):
            logger.debug(f"Cache hit for {cache_key}")
            return self.cache.get_path(cache_key, category="srtm")

        logger.debug(f"Cache miss for {cache_key}")

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
                    logger.info("Fetched SRTM successfully")
                    return self.cache.save(cache_key, data, category="srtm")
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to fetch SRTM: {response.status} - {error_text}")
                    raise Exception(f"Failed to fetch SRTM: {response.status} - {error_text}")

    def transform_to_grid(self, data_path, coordinate_manager):
        """Loads the GeoTIFF and reprojects it to the UTM grid defined by coordinate_manager."""
        dst_crs = f"EPSG:{coordinate_manager.utm_epsg}"
        
        with rasterio.open(data_path) as src:
            transform, width, height = calculate_default_transform(
                src.crs, dst_crs, src.width, src.height, *src.bounds
            )
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': dst_crs,
                'transform': transform,
                'width': width,
                'height': height
            })

            destination = np.zeros((height, width), src.dtypes[0])

            reproject(
                source=rasterio.band(src, 1),
                destination=destination,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=dst_crs,
                resampling=Resampling.bilinear
            )
            
            return destination