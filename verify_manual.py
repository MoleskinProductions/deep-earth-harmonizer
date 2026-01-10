import asyncio
from deep_earth.logging_config import setup_logging
from deep_earth.providers.osm import OverpassAdapter
from deep_earth.bbox import BoundingBox

async def main():
    setup_logging()
    # lat_min, lat_max, lon_min, lon_max
    bbox = BoundingBox(44.97, 44.98, -93.23, -93.22)
    adapter = OverpassAdapter()
    print("Fetching data...")
    data = await adapter.fetch(bbox, 10.0)
    print(f"Fetched {len(data['elements'])} elements.")

if __name__ == "__main__":
    asyncio.run(main())