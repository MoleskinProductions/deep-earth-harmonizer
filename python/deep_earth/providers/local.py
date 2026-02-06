import os
import glob
import logging
import rasterio
import numpy as np
import shutil
from typing import Any, Union, Dict, Optional, List
from pathlib import Path

from deep_earth.region import RegionContext
from deep_earth.cache import CacheManager
from .base import DataProviderAdapter
from deep_earth.harmonize import Harmonizer

logger = logging.getLogger(__name__)

class LocalFileAdapter(DataProviderAdapter):
    """
    Adapter for ingesting local geospatial data (rasters).
    Scans a directory for valid raster files associated with a region.
    Currently, it processes the first valid raster found or needs specific logic for mosaicking.
    For this implementation, we will mosaic all valid TIFs found in the directory that overlap the bbox.
    """

    def __init__(self, cache: Optional[CacheManager] = None):
        """
        Initialize the Local File adapter.
        
        Args:
            cache: Optional CacheManager. If provided, we can cache the result.
        """
        self.cache = cache

    def validate_credentials(self) -> bool:
        """Local files require no credentials."""
        return True

    def get_cache_key(self, bbox: RegionContext, resolution: float, local_dir: str = "") -> str:
        """Generates a cache key based on the directory hash and bbox."""
        # Simple hash of the directory path
        import hashlib
        dir_hash = hashlib.md5(local_dir.encode('utf-8')).hexdigest()
        return f"local_{dir_hash}_{bbox.lat_min}_{bbox.lat_max}_{bbox.lon_min}_{bbox.lon_max}_{resolution}"

    async def fetch(self, bbox: RegionContext, resolution: float, local_path: str = "") -> Optional[str]:
        """
        Scans values in local_path (file or directory).
        If multiple files are found, they are merged/mosaicked into a single GeoTIFF
        reprojected to the target bbox/resolution and saved to cache (or a temp location).
        
        Args:
            bbox: Target region.
            resolution: Target resolution.
            local_path: Path to file or directory.

        Returns:
            Path to the harmonized GeoTIFF, or None if no valid data found.
        """
        if not local_path or not os.path.exists(local_path):
            logger.warning(f"Local path does not exist: {local_path}")
            return None

        # 1. Identify source files
        source_files = []
        if os.path.isfile(local_path):
            source_files.append(local_path)
        else:
            # Recursive scan for TIFs
            for ext in ["**/*.tif", "**/*.tiff", "**/*.jp2"]:
                source_files.extend(glob.glob(os.path.join(local_path, ext), recursive=True))

        if not source_files:
            logger.warning(f"No raster files found in {local_path}")
            return None

        logger.info(f"Found {len(source_files)} potential local raster files.")

        # 2. Check overlap (optimization: skip files that don't overlap)
        # For now, we'll let rasterio.merge or reproject handle it, but checking bounds is better.
        # We will use Harmonizer logic to reproject/mosaic.
        
        # Since we need to return a single file path conforming to the grid, the easiest way
        # is to perform the "harmonization" (reprojection/resampling) right here and save to cache.

        # We'll rely on the cache to store the result.
        if self.cache:
            cache_key = self.get_cache_key(bbox, resolution, local_path)
            if self.cache.exists(cache_key, category="local"):
                logger.debug(f"Cache hit for local data: {cache_key}")
                return self.cache.get_path(cache_key, category="local")

        try:
            # We need to create a Harmonizer-like target grid to project into
            # We can reuse the header generation logic from Harmonizer
            
            # Or simplified: use rasterio.warp.reproject to a new array
            
            # Let's use a temporary in-memory method to merge, then reproject.
            # Actually, rasterio.merge.merge handles mosaicking, but we also need reprojection.
            
            # Helper: reproject everything to the target CRS/Transform and merge.
            # Because this can be memory intensive, we might want to iterate.
            
            # For this MVP agent, let's implement a simple loop:
            # 1. Initialize destination array (zeros) based on bbox/resolution
            utm_bbox = bbox.get_utm_bbox()
            x_min, y_min, x_max, y_max = utm_bbox
            width = int(np.ceil((x_max - x_min) / resolution))
            height = int(np.ceil((y_max - y_min) / resolution))
            dst_transform = rasterio.transform.from_bounds(x_min, y_min, x_max, y_max, width, height)
            dst_crs = f"EPSG:{bbox.utm_epsg}"
            
            # We don't know the band count yet. Open the first file to check.
            with rasterio.open(source_files[0]) as src0:
                count = src0.count
                dtype = src0.dtypes[0]
            
            # Initialize accumulation array
            # Note: We might want headers/footers to handle mean/max? Default to "overwrite" or "max"?
            # Rasterio merge does "last pixel wins" by default.
            
            # Let's do a trick: we will warp each source file into the destination grid.
            # This is effectively "harmonizing on the fly".
            
            dest_array = np.zeros((count, height, width), dtype=dtype)
            
            success_count = 0
            for fpath in source_files:
                try:
                    with rasterio.open(fpath) as src:
                        # Reproject into our buffer
                        # We use 'max' merging or just 'overwrite' (default).
                        # To support sparse data merging properly, we might need a mask.
                        # For now, use simple Reprojection.
                        rasterio.warp.reproject(
                            source=rasterio.band(src, list(range(1, count + 1))),
                            destination=dest_array,
                            src_transform=src.transform,
                            src_crs=src.crs,
                            dst_transform=dst_transform,
                            dst_crs=dst_crs,
                            resampling=rasterio.warp.Resampling.bilinear
                        )
                        success_count += 1
                except Exception as e:
                    logger.warning(f"Failed to process local file {fpath}: {e}")

            if success_count == 0:
                return None

            # 3. Save to cache
            if self.cache:
                with self.cache.open_write(cache_key, category="local", ext="tif") as dst_path:
                    with rasterio.open(
                        dst_path, 'w',
                        driver='GTiff',
                        height=height, width=width,
                        count=count, dtype=dtype,
                        crs=dst_crs,
                        transform=dst_transform
                    ) as dst:
                        dst.write(dest_array)
                    return dst_path
            else:
                # No cache provided (unlikely in this app), return None or raise
                return None

        except Exception as e:
            logger.error(f"Local fetch failed: {e}")
            return None

    def transform_to_grid(self, data_path: str, target_grid: Any) -> np.ndarray:
        """
        Transforms the raw fetched data to the target grid format.
        Since fetch() already harmonizes it, we just read it.
        """
        with rasterio.open(data_path) as src:
            return src.read()
