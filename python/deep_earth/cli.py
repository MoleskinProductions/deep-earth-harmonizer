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

async def run_fetch_all(bbox: RegionContext, resolution: float, year: int) -> Dict[str, Any]:
    """Fetch all data sources for the given bbox.

    Args:
        bbox: Target bounding box.
        resolution: Requested master resolution.
        year: Year for embeddings.

    Returns:
        Dictionary with ``results`` (provider -> path or None) and
        ``errors`` (provider -> error message) keys.
    """
    config = Config()
    creds = CredentialsManager()
    cache = CacheManager(config.cache_path)

    srtm_a = SRTMAdapter(creds, cache)
    gee_a = EarthEngineAdapter(creds, cache)
    osm_a = OverpassAdapter(cache_dir=config.cache_path)

    results: Dict[str, Optional[str]] = {}
    errors: Dict[str, str] = {}

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
            out_name = "osm" if name == "osm_data" else name
            results[out_name] = None
            errors[out_name] = str(result)
        elif result is None:
            out_name = "osm" if name == "osm_data" else name
            results[out_name] = None
            errors[out_name] = "provider returned no data"
        else:
            if name == "osm_data":
                results["osm"] = cache.get_path(
                    osm_a.get_cache_key(bbox, resolution), "osm", "json",
                )
            else:
                results[name] = cast(str, result)

    output: Dict[str, Any] = {"results": results}
    if errors:
        output["errors"] = errors
    return output

def main_logic(args: argparse.Namespace) -> None:
    """Main execution logic for the CLI.

    Args:
        args: Parsed command line arguments.
    """
    setup_logging()

    # Parse bbox: "lat_min,lon_min,lat_max,lon_max"
    try:
        lat_min, lon_min, lat_max, lon_max = map(float, args.bbox.split(","))
        bbox = RegionContext(lat_min, lat_max, lon_min, lon_max)
    except ValueError:
        print(
            f"Error: Invalid bbox format '{args.bbox}'. "
            "Expected 'lat_min,lon_min,lat_max,lon_max'",
        )
        sys.exit(1)

    try:
        output = asyncio.run(
            run_fetch_all(bbox, args.resolution, args.year),
        )
    except Exception as exc:
        logger.error(f"Fatal error: {exc}")
        print(json.dumps({"error": str(exc)}))
        sys.exit(1)

    # Output JSON summary
    print(json.dumps(output, indent=2))

def run_setup_wizard(args: argparse.Namespace) -> None:
    """Run the setup wizard for configuring Deep Earth."""
    from deep_earth.setup_wizard import setup_wizard
    setup_wizard(
        generate_template=getattr(args, 'generate_template', False),
        output_path=getattr(args, 'output', None)
    )

def main() -> None:
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Deep Earth Harmonizer - Multi-modal geospatial data synthesizer for Houdini"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Fetch command (default behavior)
    fetch_parser = subparsers.add_parser("fetch", help="Fetch geospatial data for a region")
    fetch_parser.add_argument("--bbox", type=str, required=True, help="lat_min,lon_min,lat_max,lon_max")
    fetch_parser.add_argument("--resolution", type=float, default=10.0, help="Resolution in meters (default: 10.0)")
    fetch_parser.add_argument("--year", type=int, default=2023, help="Embedding year (default: 2023)")
    fetch_parser.add_argument("--output-dir", type=str, help="Optional output directory (currently uses cache)")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Run the setup wizard")
    setup_parser.add_argument("--generate-template", action="store_true", help="Generate template files without prompts")
    setup_parser.add_argument("--output", "-o", type=str, help="Output path for generated files")

    # Support legacy direct --bbox usage
    parser.add_argument("--bbox", type=str, help="lat_min,lon_min,lat_max,lon_max (legacy, use 'fetch' subcommand)")
    parser.add_argument("--resolution", type=float, default=10.0, help=argparse.SUPPRESS)
    parser.add_argument("--year", type=int, default=2023, help=argparse.SUPPRESS)
    parser.add_argument("--output-dir", type=str, help=argparse.SUPPRESS)

    args = parser.parse_args()

    if args.command == "setup":
        run_setup_wizard(args)
    elif args.command == "fetch" or args.bbox:
        main_logic(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
