import ee
import os
import asyncio
import numpy as np
import rasterio
import aiohttp
import logging
from typing import Any, Union, Dict, Optional, cast

from deep_earth.bbox import BoundingBox
from deep_earth.retry import fetch_with_retry
from deep_earth.credentials import CredentialsManager
from deep_earth.cache import CacheManager
from .base import DataProviderAdapter

logger = logging.getLogger(__name__)


class EarthEngineAdapter(DataProviderAdapter):
    """
    Adapter for Google Earth Engine (GEE) to fetch 64D satellite embeddings.
    """
    
    def __init__(self, credentials: CredentialsManager, cache: CacheManager):
        """
        Initialize the Earth Engine adapter.

        Args:
            credentials: Credentials manager instance.
            cache: Cache manager instance.
        """
        self.credentials = credentials
        self.cache = cache
        
        # Initialize EE
        service_account = self.credentials.get_ee_service_account()
        key_file = self.credentials.get_ee_key_file()
        
        if service_account and key_file:
            try:
                ee_creds = ee.ServiceAccountCredentials(service_account, key_file) # type: ignore
                ee.Initialize(ee_creds)
            except Exception as e:
                logger.error(f"Failed to initialize Earth Engine: {e}")
                # We don't raise here to allow DEM-only cooks, per hardening spec
        else:
            logger.warning("Earth Engine credentials missing. GEE features will be unavailable.")

    def get_cache_key(self, bbox: BoundingBox, resolution: float, year: int = 2023) -> str:
        """
        Generates a unique cache key for GEE embeddings.

        Args:
            bbox: Target bounding box.
            resolution: Requested resolution.
            year: Year of the annual composite.

        Returns:
            Cache key string.
        """
        return f"gee_{bbox.lat_min}_{bbox.lat_max}_{bbox.lon_min}_{bbox.lon_max}_{resolution}_{year}"

    def validate_credentials(self) -> bool:
        """Validates GEE access."""
        try:
            # Check for a known asset
            ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL").limit(1).getInfo() # type: ignore
            return True
        except Exception:
            return False

    async def fetch(self, bbox: BoundingBox, resolution: float, year: int = 2023) -> str:
        """
        Fetches GEE embeddings and returns the path to the cached GeoTIFF.

        Args:
            bbox: Target bounding box.
            resolution: Requested resolution.
            year: Year of embeddings.

        Returns:
            Absolute path to the cached GeoTIFF file.
        """
        logger.info(f"Fetching EarthEngine embeddings for bbox {bbox} at resolution {resolution}, year {year}")
        cache_key = self.get_cache_key(bbox, resolution, year)
        
        if self.cache.exists(cache_key, category="embeddings"):
            logger.debug(f"Cache hit for {cache_key}")
            path = self.cache.get_path(cache_key, category="embeddings")
            if path: return path

        logger.debug(f"Cache miss for {cache_key}")

        # Define geometry
        region = ee.Geometry.Rectangle([bbox.lon_min, bbox.lat_min, bbox.lon_max, bbox.lat_max]) # type: ignore
        
        # Load embedding collection and filter by year
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        collection = ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL").filterDate(start_date, end_date) # type: ignore
        
        if collection.size().getInfo() == 0:
            raise ValueError(f"No embeddings found for year {year}")
            
        image = collection.mosaic().clip(region)
        
        # Reproject to UTM
        dst_crs = f"EPSG:{bbox.utm_epsg}"
        image = image.reproject(crs=dst_crs, scale=resolution)
        
        # Export and poll
        return await self._export_and_poll(image, region, cache_key)

    async def _export_and_poll(self, image: Any, region: Any, cache_key: str) -> str:
        """
        Exports the image to a download URL and polls for completion.

        Args:
            image: Processed EE Image.
            region: Clipping region.
            cache_key: Key for saving to cache.

        Returns:
            Path to the saved cache file.
        """
        # Get download URL (this is a direct download for small regions)
        # For larger regions, we'd use ee.batch.Export.image.toDrive or toCloudStorage
        try:
            url = image.getDownloadURL({
                'scale': image.projection().nominalScale().getInfo(),
                'crs': image.projection().crs().getInfo(),
                'format': 'GeoTIFF'
            })
            
            logger.info(f"Downloading GEE export from {url}")
            
            async with aiohttp.ClientSession() as session:
                data = await fetch_with_retry(session, url)
                logger.info("Fetched GEE embeddings successfully")
                return self.cache.save(cache_key, data, category="embeddings")
        except Exception as e:
            logger.error(f"GEE Export failed: {e}")
            raise Exception(f"GEE Export failed: {e}")

    def transform_to_grid(self, data_path: str, target_grid: Any) -> np.ndarray:
        """
        Loads the multi-band GeoTIFF and returns a NumPy array.

        Args:
            data_path: Path to the GeoTIFF file.
            target_grid: Ignored here as resampling is handled in Harmonizer.

        Returns:
            NumPy array of shape (64, H, W).
        """
        with rasterio.open(data_path) as src:
            return cast(np.ndarray, src.read())