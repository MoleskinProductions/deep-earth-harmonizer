import asyncio
import os
import rasterio
from deep_earth.credentials import CredentialsManager
from deep_earth.cache import CacheManager
from deep_earth.config import Config
from deep_earth.coordinates import CoordinateManager
from deep_earth.providers.srtm import SRTMAdapter
 
async def verify():
    config = Config()
    creds = CredentialsManager()
    cache = CacheManager(config.cache_path)
    adapter = SRTMAdapter(creds, cache)
            
    # Test a small area in Minneapolis
    cm = CoordinateManager(lat_min=44.97, lat_max=44.98, lon_min=-93.27, lon_max=-93.26)
            
    print(f"Fetching and reprojecting SRTM...")
    path = await adapter.fetch(cm, resolution=30)
    data = adapter.transform_to_grid(path, cm)
    print(data)           
    print(f"Success! Reprojected shape: {data.shape}")
    print(f"Elevation range: {data[data > 0].min()} - {data.max()} meters")
   
    if __name__ == "__main__":
        asyncio.run(verify())
