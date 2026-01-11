import asyncio
import numpy as np
from deep_earth.logging_config import setup_logging
from deep_earth.providers.osm import OverpassAdapter
from deep_earth.bbox import BoundingBox
from deep_earth.preview import generate_preview

async def test_osm():
    setup_logging()
    # lat_min, lat_max, lon_min, lon_max
    bbox = BoundingBox(44.97, 44.98, -93.23, -93.22)
    adapter = OverpassAdapter()
    print("Fetching OSM data...")
    data = await adapter.fetch(bbox, 10.0)
    print(f"Fetched {len(data['elements'])} elements.")

def test_preview():
    print("Generating dummy elevation preview...")
    dummy_dem = np.random.rand(100, 100) * 1000
    # Note: This will open a window and block until closed
    generate_preview(dummy_dem, mode="elevation", title="Manual Verification - Elevation")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        test_preview()
    else:
        asyncio.run(test_osm())
