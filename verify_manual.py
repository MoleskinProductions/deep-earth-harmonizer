import asyncio
import numpy as np
from deep_earth.logging_config import setup_logging
from deep_earth.providers.osm import OverpassAdapter
from deep_earth.region import RegionContext as BoundingBox
from deep_earth.preview import generate_preview

async def test_all():
    setup_logging()
    # lat_min, lat_max, lon_min, lon_max
    bbox = BoundingBox(44.97, 44.98, -93.23, -93.22)
    
    print("\n--- Testing OSM ---")
    adapter = OverpassAdapter()
    data = await adapter.fetch(bbox, 10.0)
    print(f"Fetched {len(data['elements'])} elements.")

    print("\n--- Testing Local Ingestion ---")
    # Borrow logic from verify_local.py
    import tempfile
    import rasterio
    from rasterio.transform import from_origin
    
    with tempfile.TemporaryDirectory() as temp_dir:
        transform = from_origin(-93.3, 45.0, 0.0001, 0.0001)
        data = np.ones((1, 100, 100), dtype=np.float32) * 99.0
        dummy_tif = f"{temp_dir}/dummy.tif"
        
        with rasterio.open(
            dummy_tif, 'w',
            driver='GTiff',
            height=100, width=100,
            count=1, dtype=data.dtype,
            crs='EPSG:4326',
            transform=transform
        ) as dst:
            dst.write(data)
            
        # Run CLI fetch programmatically
        from deep_earth.cli import run_fetch_all
        output = await run_fetch_all(bbox, resolution=10.0, year=2023, local_dir=temp_dir)
        local_res = output.get("results", {}).get("local")
        
        if local_res:
            print(f"SUCCESS: Local file harmonized to {local_res}")
        else:
            print(f"FAILURE: Local file not processed. Errors: {output.get('errors')}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        test_preview()
    else:
        asyncio.run(test_all())
