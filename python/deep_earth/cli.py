import argparse
import asyncio
import json
import os
import sys
import logging
from typing import Dict, Any, Optional, cast

from deep_earth.region import RegionContext
from deep_earth.config import Config
from deep_earth.credentials import CredentialsManager
from deep_earth.cache import CacheManager
from deep_earth.providers.srtm import SRTMAdapter
from deep_earth.providers.earth_engine import EarthEngineAdapter
from deep_earth.providers.osm import OverpassAdapter
from deep_earth.logging_config import setup_logging

logger = logging.getLogger(__name__)

async def run_fetch_all(bbox: RegionContext, resolution: float, year: int) -> Dict[str, Optional[str]]:
    """
    Fetch all data sources for the given bbox.

    Args:
        bbox: Target bounding box.
        resolution: Requested master resolution.
        year: Year for embeddings.

    Returns:
        Dictionary mapping provider names to cached file paths.
    """
    config = Config()
    creds = CredentialsManager()
    cache = CacheManager(config.cache_path)
    
    srtm_a = SRTMAdapter(creds, cache)
    gee_a = EarthEngineAdapter(creds, cache)
    osm_a = OverpassAdapter(cache_dir=config.cache_path)
    
    results: Dict[str, Optional[str]] = {}
    
    # Run fetches concurrently
    srtm_task = srtm_a.fetch(bbox, 30)
    gee_task = gee_a.fetch(bbox, resolution, year)
    osm_task = osm_a.fetch(bbox, resolution)
    
    tasks = [srtm_task, gee_task, osm_task]
    names = ["srtm", "embeddings", "osm_data"]
    
    # Use return_exceptions=True to prevent one failure from aborting all
    fetched_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for name, result in zip(names, fetched_results):
        if isinstance(result, Exception):
            logger.error(f"Failed to fetch {name}: {result}")
            results[name] = None
        else:
            if name == "osm_data":
                # Special case for OSM which returns a dict
                results["osm"] = cache.get_path(osm_a.get_cache_key(bbox, resolution), "osm", "json")
            else:
                results[name] = cast(str, result)
    
    return results

def main_logic(args: argparse.Namespace) -> None:
    """
    Main execution logic for the CLI.

    Args:
        args: Parsed command line arguments.
    """
    setup_logging()
    
    # Parse bbox: "lat_min,lon_min,lat_max,lon_max"
    try:
        lat_min, lon_min, lat_max, lon_max = map(float, args.bbox.split(","))
        bbox = RegionContext(lat_min, lat_max, lon_min, lon_max)
    except ValueError:
        print(f"Error: Invalid bbox format '{args.bbox}'. Expected 'lat_min,lon_min,lat_max,lon_max'")
        sys.exit(1)
        
    results = asyncio.run(run_fetch_all(bbox, args.resolution, args.year))
    
    # Output JSON summary
    print(json.dumps(results, indent=2))

def main() -> None:
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Deep Earth Harmonizer CLI")
    parser.add_argument("--bbox", type=str, required=True, help="lat_min,lon_min,lat_max,lon_max")
    parser.add_argument("--resolution", type=float, default=10.0, help="Resolution in meters (default: 10.0)")
    parser.add_argument("--year", type=int, default=2023, help="Embedding year (default: 2023)")
    parser.add_argument("--output-dir", type=str, help="Optional output directory (currently uses cache)")
    
    args = parser.parse_args()
    main_logic(args)

if __name__ == "__main__":
    main()
