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
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Lazily initialize Earth Engine only when needed."""
        if self._initialized:
            return

        service_account = self.credentials.get_ee_service_account()
        key_file = self.credentials.get_ee_key_file()
        
        if service_account and key_file:
            try:
                ee_creds = ee.ServiceAccountCredentials(service_account, key_file) # type: ignore
                ee.Initialize(ee_creds)
                self._initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize Earth Engine: {e}")
                raise RuntimeError(f"Earth Engine initialization failed: {e}")
        else:
            raise ValueError("Earth Engine credentials missing")

    def get_cache_key(self, bbox: RegionContext, resolution: float, year: int = 2023) -> str:
        """Generates a unique cache key for GEE embeddings."""
        return f"gee_{bbox.lat_min}_{bbox.lat_max}_{bbox.lon_min}_{bbox.lon_max}_{resolution}_{year}"

    def validate_credentials(self) -> bool:
        """Validates GEE access."""
        try:
            self._ensure_initialized()
            # Check for a known asset
            ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL").limit(1).getInfo() # type: ignore
            return True
        except Exception:
            return False

    async def fetch(self, bbox: RegionContext, resolution: float, year: int = 2023) -> str:
        """
        Fetches GEE embeddings and returns the path to the cached GeoTIFF.
        Automatically chooses between direct download and batch export based on region size.
        """
        self._ensure_initialized()
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
        
        # Check area size to decide export method
        area_km2 = bbox.area_km2()
        if area_km2 < 10.0: # Threshold for direct download: 10km2
            return await self._fetch_direct(image, region, cache_key)
        else:
            return await self._fetch_batch(image, region, cache_key)

    async def _fetch_direct(self, image: Any, region: Any, cache_key: str) -> str:
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
            raise

    async def _fetch_batch(self, image: Any, region: Any, cache_key: str) -> str:
        """Large region: use Export to GCS and poll for completion."""
        bucket = self.credentials.get_gcs_bucket()
        if not bucket:
            # If no bucket, we can try Export.toDrive, but we won't be able to download it easily
            raise ValueError("Large region detected but no GCS bucket configured for batch export.")

        file_name = f"{cache_key}_{int(time.time())}"
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
            raise RuntimeError(f"GEE Export task failed: {status.get('error_message', 'Unknown error')}")

        # Download from GCS
        return await self._download_from_gcs(bucket, f"{file_name}.tif", cache_key)

    async def _poll_task(self, task: Any, timeout_secs: int = 600) -> Dict[str, Any]:
        """Polls an EE task until completion or timeout."""
        start_time = time.time()
        wait_secs = 5
        
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
