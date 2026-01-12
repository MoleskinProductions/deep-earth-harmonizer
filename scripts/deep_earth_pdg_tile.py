"""
PDG Tile Processor for Deep Earth Harmonizer.
This script is intended to be run via hython within a TOP network.
"""

import os
import sys
import argparse
import asyncio
import numpy as np
import logging

from deep_earth.region import RegionContext
from deep_earth.harmonize import Harmonizer
from deep_earth.providers.srtm import SRTMAdapter
from deep_earth.providers.earth_engine import EarthEngineAdapter
from deep_earth.providers.osm import OverpassAdapter
from deep_earth.credentials import CredentialsManager
from deep_earth.cache import CacheManager
from deep_earth.config import Config
from deep_earth.async_utils import run_async
from deep_earth.logging_config import setup_logging

def main():
    parser = argparse.ArgumentParser(description="Process a single Deep Earth tile for PDG.")
    parser.add_argument("--bbox", type=str, required=True, help="lat_min,lon_min,lat_max,lon_max")
    parser.add_argument("--resolution", type=float, default=10.0)
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--output", type=str, required=True, help="Output .bgeo.sc path")
    parser.add_argument("--viz-mode", type=str, default="none")
    
    args = parser.parse_args()
    setup_logging()
    logger = logging.getLogger("deep_earth.pdg")

    # 1. Setup Context
    try:
        lat_min, lon_min, lat_max, lon_max = map(float, args.bbox.split(","))
        region = RegionContext(lat_min, lat_max, lon_min, lon_max)
    except ValueError as e:
        logger.error(f"Invalid bbox: {e}")
        sys.exit(1)

    config = Config()
    creds = CredentialsManager()
    cache = CacheManager(config.cache_path)
    
    srtm_a = SRTMAdapter(creds, cache)
    gee_a = EarthEngineAdapter(creds, cache)
    osm_a = OverpassAdapter(cache_dir=config.cache_path)
    harmonizer = Harmonizer(region, args.resolution)

    # 2. Fetch Data (Parallel)
    async def fetch_all():
        return await asyncio.gather(
            srtm_a.fetch(region, 30),
            gee_a.fetch(region, args.resolution, args.year),
            osm_a.fetch(region, args.resolution),
            return_exceptions=True
        )

    results = run_async(fetch_all())
    srtm_path, gee_path, osm_json = results

    # 3. Harmonize & Inject
    # We only proceed if we have a DEM at minimum
    if isinstance(srtm_path, Exception) or not srtm_path:
        logger.error(f"Failed to fetch DEM: {srtm_path}")
        sys.exit(1)

    height_grid = harmonizer.resample(srtm_path, bands=1)
    
    embed_grid = None
    if not isinstance(gee_path, Exception) and gee_path:
        embed_grid = harmonizer.resample(gee_path, bands=list(range(1, 65)))
    else:
        logger.warning(f"GEE failed or skipped: {gee_path}")
        embed_grid = np.zeros((64, harmonizer.height, harmonizer.width), dtype=np.float32)

    if not isinstance(osm_json, Exception) and osm_json:
        osm_layers = osm_a.transform_to_grid(osm_json['elements'], harmonizer)
        harmonizer.add_layers(osm_layers)

    # Add Data Quality
    quality = harmonizer.compute_quality_layer(
        height_grid, 
        embed_grid if not isinstance(gee_path, Exception) else None
    )
    harmonizer.add_layers({"data_quality": quality})

    # 4. Save Geometry (Requires hou)
    try:
        import hou
        from deep_earth.houdini.geometry import inject_heightfield
        
        # Create a temp geometry object
        # Note: In PDG, we usually use a 'Geometry' object or 'hou.Node.geometry()'
        geo = hou.Geometry()
        
        viz_mode = args.viz_mode.lower() if args.viz_mode.lower() != "none" else None
        
        inject_heightfield(
            geo, region, harmonizer, height_grid, embed_grid, 
            viz_mode=viz_mode,
            provenance={"year": args.year, "pdg_tile": True}
        )
        
        # Save to disk
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        geo.save(args.output)
        logger.info(f"Saved tile geometry to {args.output}")
        
    except ImportError:
        logger.error("Houdini (hou module) not found. Cannot save .bgeo.sc")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to save geometry: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
