import ee
import os
import asyncio
import numpy as np
import rasterio
import aiohttp
from .base import DataProviderAdapter

class EarthEngineAdapter(DataProviderAdapter):
    def __init__(self, credentials, cache):
        self.credentials = credentials
        self.cache = cache
        
        # Initialize EE
        service_account = self.credentials.get_ee_service_account()
        key_file = self.credentials.get_ee_key_file()
        
        if service_account and key_file:
            ee_creds = ee.ServiceAccountCredentials(service_account, key_file)
            ee.Initialize(ee_creds)
        else:
            raise ValueError("Earth Engine credentials missing")

    def get_cache_key(self, bbox, resolution, year=2023):
        return f"gee_{bbox.lat_min}_{bbox.lat_max}_{bbox.lon_min}_{bbox.lon_max}_{resolution}_{year}"

    def validate_credentials(self):
        try:
            # Check for a known asset
            ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL").limit(1).getInfo()
            return True
        except:
            return False

    async def fetch(self, bbox, resolution, year=2023):
        """Fetches GEE embeddings and returns the path to the cached file."""
        cache_key = self.get_cache_key(bbox, resolution, year)
        
        if self.cache.exists(cache_key, category="embeddings"):
            return self.cache.get_path(cache_key, category="embeddings")

        # Define geometry
        region = ee.Geometry.Rectangle([bbox.lon_min, bbox.lat_min, bbox.lon_max, bbox.lat_max])
        
        # Load embedding collection and filter by year
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        collection = ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL").filterDate(start_date, end_date)
        
        if collection.size().getInfo() == 0:
            raise ValueError(f"No embeddings found for year {year}")
            
        image = collection.mosaic().clip(region)
        
        # Reproject to UTM
        dst_crs = f"EPSG:{bbox.utm_epsg}"
        image = image.reproject(crs=dst_crs, scale=resolution)
        
        # Export and poll
        return await self._export_and_poll(image, region, cache_key)

    async def _export_and_poll(self, image, region, cache_key):
        """Exports the image to a download URL and polls for completion."""
        # Get download URL (this is a direct download for small regions)
        # For larger regions, we'd use ee.batch.Export.image.toDrive or toCloudStorage
        try:
            url = image.getDownloadURL({
                'scale': image.projection().nominalScale().getInfo(),
                'crs': image.projection().crs().getInfo(),
                'format': 'GeoTIFF'
            })
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.read()
                        return self.cache.save(cache_key, data, category="embeddings")
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to download GEE export: {response.status} - {error_text}")
        except Exception as e:
            raise Exception(f"GEE Export failed: {e}")

    def transform_to_grid(self, data_path, coordinate_manager):
        """Loads the multi-band GeoTIFF and returns a NumPy array."""
        with rasterio.open(data_path) as src:
            return src.read()