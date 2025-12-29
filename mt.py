import asyncio
import os
import rasterio
from deep_earth.credentials import CredentialsManager
from deep_earth.cache import CacheManager
from deep_earth.config import Config
from deep_earth.coordinates import CoordinateManager
from deep_earth.providers.earth_engine import EarthEngineAdapter
  
async def verify():
    print("--- GEE Manual Verification ---")
    config = Config()
    creds = CredentialsManager()
    cache = CacheManager(config.cache_path)
    adapter = EarthEngineAdapter(creds, cache)
         
          # 100m box in Minneapolis
    cm = CoordinateManager(lat_min=44.977, lat_max=44.978, lon_min=-93.265, lon_max=-93.264)
            
    print(f"Fetching GEE Embeddings...")
    path = await adapter.fetch(cm, resolution=10, year=2023)
    print(f"Success! Data cached at: {path}")
     
    with rasterio.open(path) as src:
        print(f"Bands: {src.count}")
        if src.count == 64:
            print("Verification: SUCCESS")
        else:
            print(f"Verification: FAILED (Expected 64 bands, got {src.count})")
    
if __name__ == "__main__":
    asyncio.run(verify())
