import ee
import os
import asyncio
import numpy as np
import rasterio
import aiohttp
import logging
import time
from typing import Any, Union, Dict, Optional, cast
from google.cloud import storage

from deep_earth.region import RegionContext
from deep_earth.retry import fetch_with_retry
from deep_earth.credentials import CredentialsManager
from deep_earth.cache import CacheManager
from .base import DataProviderAdapter

logger = logging.getLogger(__name__)


class EarthEngineAdapter(DataProviderAdapter):
    """
    Adapter for Google Earth Engine (GEE) to fetch 64D satellite embeddings.
    Supports scaling to large regions via batch exports to Google Cloud Storage.

    Follows fail-graceful design: initialization and fetch errors are logged
    and surfaced as ``None`` return values rather than exceptions, so that
    DEM/OSM-only pipelines can continue when GEE is unavailable.
    """

    @staticmethod
    def require_ee(func):
        """Decorator to ensure Earth Engine is initialized before calling a method."""
        import asyncio as _asyncio
        import functools

        if _asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def wrapper(self, *args, **kwargs):
                if not self._ensure_initialized():
                    logger.warning(
                        f"Skipping {func.__name__} — "
                        f"initialization failed: "
                        f"{self._init_error}"
                    )
                    return None
                return await func(self, *args, **kwargs)
        else:
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                if not self._ensure_initialized():
                    logger.warning(
                        f"Skipping {func.__name__} — "
                        f"initialization failed: "
                        f"{self._init_error}"
                    )
                    return None if func.__name__ == 'fetch' else False
                return func(self, *args, **kwargs)
        return wrapper

    def __init__(self, credentials: CredentialsManager, cache: CacheManager):
        """
        Initialize the Earth Engine adapter.

        Args:
            credentials: Credentials manager instance.
            cache: Cache manager instance.
        """
        self.credentials = credentials
        self.cache = cache
        self._initialized = False
        self._init_error: Optional[str] = None

    def _ensure_initialized(self) -> bool:
        """Lazily initialize Earth Engine only when needed.

        Returns:
            True if initialization succeeded, False otherwise.
        """
        if self._initialized:
            return True

        if self._init_error is not None:
            return False

        service_account = self.credentials.get_ee_service_account()
        key_file = self.credentials.get_ee_key_file()

        if service_account and key_file:
            try:
                ee_creds = ee.ServiceAccountCredentials(service_account, key_file) # type: ignore
                ee.Initialize(ee_creds)
                self._initialized = True
                return True
            except Exception as e:
                self._init_error = str(e)
                logger.error(f"Failed to initialize Earth Engine: {e}")
                return False
        else:
            self._init_error = "Earth Engine credentials missing"
            logger.warning(self._init_error)
            return False

    @staticmethod
    def get_available_datasets() -> list[Dict[str, str]]:
        """Returns a list of curated Earth Engine datasets."""
        return [
            {"id": "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL", "label": "Google Satellite Embeddings (64D)", "type": "embedding"},
            {"id": "COPERNICUS/S2_SR_HARMONIZED", "label": "Sentinel-2 (10m Optical)", "type": "image"},
            {"id": "LANDSAT/LC09/C02/T1_L2", "label": "Landsat 9 (30m Optical)", "type": "image"},
            {"id": "GOOGLE/DYNAMICWORLD/V1", "label": "Dynamic World (LULC Probabilities)", "type": "image"},
            {"id": "ESA/WorldCover/v100", "label": "ESA WorldCover (10m Land Cover)", "type": "image"},
            {"id": "NASA/NASADEM_HGT/001", "label": "NASADEM (30m Elevation)", "type": "image"},
            {"id": "JAXA/ALOS/AW3D30/V2_2", "label": "ALOS World 3D (30m DSM)", "type": "image"},
            {"id": "ECMWF/ERA5_LAND/HOURLY", "label": "ERA5 Land (Climate)", "type": "image"},
            {"id": "MODIS/006/MCD12Q1", "label": "MODIS Land Cover (500m)", "type": "image"},
            {"id": "UMD/hansen/global_forest_change_2023_v1_11", "label": "Global Forest Change", "type": "image"},
            {"id": "USGS/SRTMGL1_003", "label": "USGS SRTM (30m Elevation)", "type": "image"},
        ]

    def get_cache_key(self, bbox: RegionContext, resolution: float, year: int = 2023, asset_id: str = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL") -> str:
        """Generates a unique cache key for GEE embeddings."""
        safe_asset = asset_id.replace("/", "_").replace(":", "_")
        return f"gee_{safe_asset}_{bbox.lat_min}_{bbox.lat_max}_{bbox.lon_min}_{bbox.lon_max}_{resolution}_{year}"

    @require_ee
    def validate_credentials(self) -> bool:
        """Validates GEE access."""
        try:
            # Check for a known asset
            ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL").limit(1).getInfo() # type: ignore
            return True
        except Exception as e:
            logger.warning(f"Earth Engine credential validation failed: {e}")
            return False

    @require_ee
    async def fetch(self, bbox: RegionContext, resolution: float, year: int = 2023, asset_id: str = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL") -> Optional[str]:
        """
        Fetches GEE data and returns the path to the cached GeoTIFF.

        Returns None (instead of raising) when initialization fails or
        data cannot be retrieved, allowing the pipeline to continue with
        degraded data quality.
        """
        # Decorator handles initialization check now via require_ee? 
        # Actually I need to apply it to the method definition not inside.
        # But wait, I am replacing the method body here. I should have replaced the definition line to add @require_ee
        # I will do that in a separate replacement chunk.
        
        logger.info(f"Fetching EarthEngine data ({asset_id}) for bbox {bbox} at resolution {resolution}, year {year}")
        cache_key = self.get_cache_key(bbox, resolution, year, asset_id)

        if self.cache.exists(cache_key, category="embeddings"):
            logger.debug(f"Cache hit for {cache_key}")
            path = self.cache.get_path(cache_key, category="embeddings")
            if path:
                return path

        logger.debug(f"Cache miss for {cache_key}")
        try:
            # Define geometry
            region = ee.Geometry.Rectangle([bbox.lon_min, bbox.lat_min, bbox.lon_max, bbox.lat_max]) # type: ignore

            # Handle different collection types
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"

            # Determine if it's an ImageCollection or Image based on basic heuristics or try/except
            # For simplicity, we assume ImageCollection for most timestamps, but some assets are single Images.
            # However, the curated list are mostly collections.
            # A more robust way is to check the asset type or just try to filter.
            
            try:
                collection = ee.ImageCollection(asset_id).filterDate(start_date, end_date) # type: ignore
                if collection.size().getInfo() == 0:
                     logger.warning(f"No data found for {asset_id} in year {year}")
                     return None
                image = collection.mosaic().clip(region)
            except Exception:
                # Fallback if it's a single image or non-temporal
                logger.debug(f"Assuming {asset_id} is a single image or non-filtered collection")
                image = ee.Image(asset_id).clip(region)

            # Reproject to UTM
            dst_crs = f"EPSG:{bbox.utm_epsg}"
            image = image.reproject(crs=dst_crs, scale=resolution)

            # Check area size to decide export method
            area_km2 = bbox.area_km2()
            if area_km2 < 10.0:
                return await self._fetch_direct(image, region, cache_key)
            else:
                return await self._fetch_batch(image, region, cache_key)
        except Exception as e:
            logger.error(f"GEE fetch failed: {e}")
            return None

    async def _fetch_direct(self, image: Any, region: Any, cache_key: str) -> Optional[str]:
        """Small region: use getDownloadURL for immediate results."""
        try:
            url = image.getDownloadURL({
                'scale': image.projection().nominalScale().getInfo(),
                'crs': image.projection().crs().getInfo(),
                'format': 'GeoTIFF'
            })

            logger.info(f"Downloading GEE direct export from {url}")
            async with aiohttp.ClientSession() as session:
                data = await fetch_with_retry(session, url)
                return self.cache.save(cache_key, data, category="embeddings")
        except Exception as e:
            if "Payload too large" in str(e) or "400" in str(e):
                logger.warning("Direct download failed due to size. Falling back to batch export.")
                return await self._fetch_batch(image, region, cache_key)
            logger.error(f"GEE Direct Export failed: {e}")
            return None

    async def _fetch_batch(self, image: Any, region: Any, cache_key: str) -> Optional[str]:
        """Large region: use Export to GCS and poll for completion."""
        bucket = self.credentials.get_gcs_bucket()
        if not bucket:
            logger.warning(
                "Large region detected but no GCS bucket configured "
                "for batch export. Skipping GEE embeddings."
            )
            return None

        file_name = f"{cache_key}_{int(time.time())}"
        try:
            task = ee.batch.Export.image.toCloudStorage(
                image=image,
                description=f"DeepEarth_{cache_key}",
                bucket=bucket,
                fileNamePrefix=file_name,
                scale=image.projection().nominalScale().getInfo(),
                crs=image.projection().crs().getInfo(),
                format='GeoTIFF'
            )

            task.start()
            logger.info(f"Started GEE batch export task {task.id} to gs://{bucket}/{file_name}.tif")

            # Poll for completion
            status = await self._poll_task(task)
            if status['state'] != 'COMPLETED':
                error_msg = status.get('error_message', 'Unknown error')
                logger.error(f"GEE Export task failed: {error_msg}")
                return None

            # Download from GCS
            return await self._download_from_gcs(bucket, f"{file_name}.tif", cache_key)
        except Exception as e:
            logger.error(f"GEE batch export failed: {e}")
            return None

    async def _poll_task(self, task: Any, timeout_secs: int = 600) -> Dict[str, Any]:
        """Polls an EE task until completion or timeout."""
        start_time = time.time()
        wait_secs: float = 5.0
        
        while True:
            status = task.status()
            state = status['state']
            
            if state in ['COMPLETED', 'FAILED', 'CANCELLED']:
                return cast(Dict[str, Any], status)
            
            if time.time() - start_time > timeout_secs:
                task.cancel()
                raise TimeoutError(f"GEE export task {task.id} timed out after {timeout_secs}s")
            
            logger.debug(f"GEE Task {task.id} state: {state}. Waiting {wait_secs}s...")
            await asyncio.sleep(wait_secs)
            wait_secs = min(wait_secs * 1.5, 30) # Exponential backoff for polling

    async def _download_from_gcs(self, bucket_name: str, blob_name: str, cache_key: str) -> str:
        """Downloads a file from GCS using credentials from manager."""
        key_file = self.credentials.get_ee_key_file()
        if not key_file:
            raise ValueError("GCS credentials missing")
            
        client = storage.Client.from_service_account_json(key_file)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        logger.info(f"Downloading {blob_name} from GCS bucket {bucket_name}")
        data = blob.download_as_bytes()
        
        # Cleanup GCS
        try:
            blob.delete()
        except Exception as e:
            logger.warning(f"Failed to delete blob {blob_name} from GCS: {e}")
            
        return self.cache.save(cache_key, data, category="embeddings")

    def transform_to_grid(self, data_path: str, target_grid: Any) -> np.ndarray:
        """Loads the multi-band GeoTIFF and returns a NumPy array."""
        with rasterio.open(data_path) as src:
            return cast(np.ndarray, src.read())
