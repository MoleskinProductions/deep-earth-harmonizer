import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import rasterio
from rasterio.warp import Resampling, reproject

from deep_earth.region import RegionContext

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    """Structured result from a provider fetch, distinguishing success,
    missing data, and errors for fail-graceful pipelines.

    Attributes:
        provider: Name of the data provider (e.g., "srtm", "gee", "osm").
        path: Path to the cached file on success, None otherwise.
        error: Error message if the fetch failed, None on success.
    """
    provider: str
    path: Optional[str] = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        """True when fetch succeeded and path is available."""
        return self.path is not None and self.error is None

class Harmonizer:
    """
    Orchestrates the resampling and alignment of multiple geospatial data streams.
    
    Attributes:
        cm (RegionContext): Context manager for the target region.
        resolution (float): Master resolution in meters per pixel.
        width, height (int): Dimensions of the master grid.
        x_min, y_min, x_max, y_max (float): Bounding box in UTM.
        dst_transform (rasterio.Affine): Transform matrix for the master grid.
        dst_crs (str): Target Coordinate Reference System.
        layers (Dict[str, np.ndarray]): Dictionary of harmonized data layers.
    """
    
    def __init__(self, coordinate_manager: RegionContext, resolution: float = 10.0):
        """
        Initialize the Harmonizer.

        Args:
            coordinate_manager: Coordinate manager for the target region.
            resolution: Master resolution in meters.
        """
        self.cm = coordinate_manager
        self.resolution = resolution
        
        # Calculate master grid dimensions in UTM
        utm_bbox = self.cm.get_utm_bbox()
        self.x_min, self.y_min, self.x_max, self.y_max = utm_bbox
        
        self.width = int(math.ceil((self.x_max - self.x_min) / self.resolution))
        self.height = int(math.ceil((self.y_max - self.y_min) / self.resolution))
        
        self.dst_transform = rasterio.transform.from_bounds(
            self.x_min, self.y_min, self.x_max, self.y_max, self.width, self.height
        )
        self.dst_crs = f"EPSG:{self.cm.utm_epsg}"
        
        self.layers: Dict[str, np.ndarray] = {}

    def resample(self, src_path: str, bands: Optional[Union[int, List[int]]] = None) -> np.ndarray:
        """
        Resamples the given source GeoTIFF to the master grid.

        Args:
            src_path: Path to the source GeoTIFF file.
            bands: Single band index, list of band indices, or None for all bands.

        Returns:
            NumPy array of the resampled data.
        """
        with rasterio.open(src_path) as src:
            if bands is None:
                # Auto-detect all bands
                band_indices = list(range(1, src.count + 1))
                band_count = src.count
            elif isinstance(bands, int):
                band_indices = [bands]
                band_count = 1
            else:
                band_indices = bands
                band_count = len(bands)

            if band_count == 1:
                dst_shape = (self.height, self.width)
            else:
                dst_shape = (band_count, self.height, self.width)
                
            destination = np.zeros(dst_shape, src.dtypes[0])
            
            reproject(
                source=rasterio.band(src, band_indices),
                destination=destination,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=self.dst_transform,
                dst_crs=self.dst_crs,
                resampling=Resampling.bilinear if src.dtypes[0] != 'int' else Resampling.nearest
            )
            
            return destination

    def add_layers(self, layers_dict: Dict[str, np.ndarray]) -> None:
        """
        Adds multiple layers to the harmonizer.
        Each layer must be a NumPy array with (height, width) matching the master grid.

        Args:
            layers_dict: Dictionary mapping layer names to NumPy arrays.
        """
        for name, data in layers_dict.items():
            if data.shape != (self.height, self.width):
                raise ValueError(f"Layer dimensions {data.shape} do not match master grid {(self.height, self.width)}")
            self.layers[name] = data

    def process_fetch_result(
        self,
        result: Any,
        provider_name: str,
        bands: Optional[Union[int, List[int]]] = None,
    ) -> Tuple[Optional[np.ndarray], FetchResult]:
        """Safely resample a provider result into a grid.

        Handles ``None`` paths, ``Exception`` objects (from
        ``asyncio.gather(return_exceptions=True)``), and file-read
        errors without raising.

        Args:
            result: The raw return from a provider fetch — a file path
                (str), ``None``, or an ``Exception``.
            provider_name: Human-readable provider name for logging.
            bands: Band(s) to resample.

        Returns:
            A tuple of (grid_or_None, FetchResult).
        """
        if isinstance(result, Exception):
            msg = f"{provider_name} fetch raised: {result}"
            logger.error(msg)
            return None, FetchResult(provider_name, error=msg)

        if result is None:
            msg = f"{provider_name} returned no data"
            logger.warning(msg)
            return None, FetchResult(provider_name, error=msg)

        try:
            grid = self.resample(result, bands=bands)
            return grid, FetchResult(provider_name, path=result)
        except Exception as e:
            msg = f"{provider_name} resample failed: {e}"
            logger.error(msg)
            return None, FetchResult(provider_name, error=msg)

    def compute_quality_layer(self, height_grid: Optional[np.ndarray] = None, embed_grid: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Computes a data quality score (0.0 - 1.0) for each grid cell.
        Uses weights defined in Config.
        """
        from deep_earth.config import Config
        weights = Config().quality_weights

        quality = np.zeros((self.height, self.width), dtype=np.float32)
        
        has_dem = height_grid is not None
        has_embed = embed_grid is not None
        has_osm = "highway" in self.layers or "landuse" in self.layers
        
        if has_dem:
            quality += weights.get("dem_only", 0.25)
            
        if has_embed:
            # Note: Logic here is additive, original was simplistic.
            # If we want exactly the weights:
            # "dem_plus_embed": 0.75 means DEM (0.25) + Embed (0.5).
            # So adding 0.5 for embed is correct if base is 0.25.
            # But relying on specific additive keys being "dem_plus_..." is slightly confusing if we just add.
            # Let's assume the weights represent the incremental value or total state?
            # Original code:
            # if has_dem: quality += 0.25
            # if has_embed: quality += 0.5
            # if has_osm: quality += 0.25
            # Total = 1.0
            
            # If Config says "dem_plus_embed": 0.75, it implies the SUM.
            # So we should probably derive increments or change logic to check combination.
            # For simplicity in this refactor, I will stick to additive logic but use keys that implied increments if possible,
            # OR just re-interpret the keys.
            
            # Let's define additive weights for simplicity.
            # dem_weight = 0.25
            # embed_weight = 0.5
            # osm_weight = 0.25
            
            # Using the config dict keys I created:
            # "dem_only": 0.25 -> implies DEM contribution is 0.25
            # "dem_plus_osm": 0.5 -> implies OSM contribution is 0.5 - 0.25 = 0.25
            # "dem_plus_embed": 0.75 -> implies Embed contribution is 0.75 - 0.25 = 0.5
            
            # I will use that logic.
            pass

        quality_incr = 0.0
        if has_dem:
            quality_incr += weights.get("dem_only", 0.25)
        if has_osm:
            # (dem + osm) - dem
            quality_incr += (weights.get("dem_plus_osm", 0.5) - weights.get("dem_only", 0.25))
        if has_embed:
             # (dem + embed) - dem
             quality_incr += (weights.get("dem_plus_embed", 0.75) - weights.get("dem_only", 0.25))
        
        quality += quality_incr
            
        return quality