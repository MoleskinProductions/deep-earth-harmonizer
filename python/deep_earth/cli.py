import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, cast

from deep_earth.cache import CacheManager
from deep_earth.config import Config
from deep_earth.credentials import CredentialsManager
from deep_earth.logging_config import setup_logging
from deep_earth.providers.base import DataProviderAdapter
from deep_earth.providers.earth_engine import EarthEngineAdapter
from deep_earth.providers.local import LocalFileAdapter
from deep_earth.providers.osm import OverpassAdapter
from deep_earth.providers.srtm import SRTMAdapter
from deep_earth.region import RegionContext

logger = logging.getLogger(__name__)


class CLIError(Exception):
    """Raised when the CLI encounters an error that should exit."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code

async def run_fetch_all(
    bbox: RegionContext, 
    resolution: float, 
    year: int,
    dataset_id: str = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL",
    local_dir: Optional[str] = None,
    adapters: Optional[Dict[str, DataProviderAdapter]] = None
) -> Dict[str, Any]:
    """Fetch all data sources for the given bbox.

    Args:
        bbox: Target bounding box.
        resolution: Requested master resolution.
        year: Year for embeddings.
        dataset_id: Earth Engine dataset ID.
        local_dir: Path to directory for local raster ingestion.
        adapters: Optional dictionary of injected adapters (for testing).

    Returns:
        Dictionary with ``results`` (provider -> path or None) and
        ``errors`` (provider -> error message) keys.
    """
    if adapters is None:
        config = Config()
        creds = CredentialsManager()
        cache = CacheManager(config.cache_path)

        adapters = {
            "srtm": SRTMAdapter(creds, cache),
            "gee": EarthEngineAdapter(creds, cache),
            "osm": OverpassAdapter(cache_dir=config.cache_path),
            "local": LocalFileAdapter(cache)
        }
    
    # Extract adapters (safe cast as we know the keys if created above)
    srtm_a = adapters["srtm"]
    gee_a = cast(EarthEngineAdapter, adapters["gee"])
    osm_a = cast(OverpassAdapter, adapters["osm"])
    local_a = cast(LocalFileAdapter, adapters.get("local"))

    results: Dict[str, Optional[str]] = {}
    errors: Dict[str, str] = {}

    # Run fetches concurrently
    # Note: validation logic can be moved here or kept in adapters
    
    tasks = [
        srtm_a.fetch(bbox, 30),
        gee_a.fetch(bbox, resolution, year, dataset_id),
        osm_a.fetch(bbox, resolution)
    ]
    names = ["srtm", "embeddings", "osm_data"]

    if local_dir and local_a:
        tasks.append(local_a.fetch(bbox, resolution, local_dir))
        names.append("local")

    # Use return_exceptions=True to prevent one failure from aborting all
    fetched_results = await asyncio.gather(*tasks, return_exceptions=True)

    config_for_osm_cache = Config() # Need config for cache key generation if not injected

    for name, result in zip(names, fetched_results):
        if isinstance(result, Exception):
            logger.error(f"Failed to fetch {name}: {result}")
            out_name = "osm" if name == "osm_data" else name
            results[out_name] = None
            errors[out_name] = str(result)
        elif result is None:
            out_name = "osm" if name == "osm_data" else name
            results[out_name] = None
            if name != "local": # Local is optional depending on args, but if task ran and return None...
                 errors[out_name] = "provider returned no data"
        else:
            if name == "osm_data":
                # OSM fetch returns data dict, not path; look up
                # cached path via the adapter's cache key.
                cache_kp = CacheManager(Config().cache_path)
                results["osm"] = cache_kp.get_path(
                    osm_a.get_cache_key(bbox, resolution),
                    "osm", "json",
                )
            else:
                results[name] = cast(str, result)

    output: Dict[str, Any] = {"results": results}
    if errors:
        output["errors"] = errors
    return output

def main_logic(args: argparse.Namespace) -> Dict[str, Any]:
    """Main execution logic for the CLI.

    Args:
        args: Parsed command line arguments.

    Returns:
        Structured output from ``run_fetch_all``.

    Raises:
        CLIError: On invalid input or fatal fetch errors.
    """
    setup_logging()

    # Parse bbox: "lat_min,lon_min,lat_max,lon_max"
    try:
        lat_min, lon_min, lat_max, lon_max = map(
            float, args.bbox.split(","),
        )
        bbox = RegionContext(lat_min, lat_max, lon_min, lon_max)
    except ValueError:
        raise CLIError(
            f"Invalid bbox format '{args.bbox}'. "
            "Expected 'lat_min,lon_min,lat_max,lon_max'"
        )

    try:
        dataset_id = getattr(
            args, "dataset_id",
            "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL",
        )
        local_dir = getattr(args, "local_dir", None)

        output = asyncio.run(
            run_fetch_all(
                bbox, args.resolution, args.year,
                dataset_id, local_dir,
            ),
        )
    except CLIError:
        raise
    except Exception as exc:
        raise CLIError(str(exc)) from exc

    # Output JSON summary
    print(json.dumps(output, indent=2))

    # Optional preview
    preview_path = getattr(args, "preview", None)
    if preview_path is not None:
        _run_preview(output, preview_path)

    return output

def _run_preview(output: Dict[str, Any], preview_path: str) -> None:
    """Generate an elevation preview from fetched SRTM data.

    Args:
        output: The structured output from ``run_fetch_all``.
        preview_path: File path to save the preview image.
    """
    srtm_path = output.get("results", {}).get("srtm")
    if not srtm_path:
        logger.warning("No SRTM data available for preview")
        return

    try:
        import rasterio
        from deep_earth.preview import generate_preview
            
        with rasterio.open(srtm_path) as src:
            dem = src.read(1)
        generate_preview(
            dem, mode="elevation",
            title="Deep Earth — Elevation Preview",
            output_path=preview_path,
        )
        print(f"Preview saved to {preview_path}")
    except Exception as exc:
        logger.error(f"Preview generation failed: {exc}")


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
    fetch_parser.add_argument("--dataset-id", type=str, default="GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL", help="Earth Engine Dataset ID")
    fetch_parser.add_argument("--local-dir", type=str, help="Directory containing local raster files for ingestion")
    fetch_parser.add_argument("--output-dir", type=str, help="Optional output directory (currently uses cache)")
    fetch_parser.add_argument("--preview", type=str, metavar="FILE", help="Save an elevation preview image to FILE (e.g. preview.png)")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Run the setup wizard")
    setup_parser.add_argument("--generate-template", action="store_true", help="Generate template files without prompts")
    setup_parser.add_argument("--output", "-o", type=str, help="Output path for generated files")

    # Support legacy direct --bbox usage
    parser.add_argument("--bbox", type=str, help="lat_min,lon_min,lat_max,lon_max (legacy, use 'fetch' subcommand)")
    parser.add_argument("--resolution", type=float, default=10.0, help=argparse.SUPPRESS)
    parser.add_argument("--year", type=int, default=2023, help=argparse.SUPPRESS)
    parser.add_argument("--dataset-id", type=str, default="GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL", help=argparse.SUPPRESS)
    parser.add_argument("--local-dir", type=str, help=argparse.SUPPRESS)
    parser.add_argument("--output-dir", type=str, help=argparse.SUPPRESS)

    args = parser.parse_args()

    if args.command == "setup":
        run_setup_wizard(args)
    elif args.command == "fetch" or args.bbox:
        try:
            main_logic(args)
        except CLIError as exc:
            print(json.dumps({"error": str(exc)}))
            sys.exit(exc.exit_code)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
