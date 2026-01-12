import numpy as np
import rasterio
import math
from typing import Dict, Optional, Union, List, Any, Tuple
from rasterio.warp import reproject, Resampling
from deep_earth.region import RegionContext

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

    def resample(self, src_path: str, bands: Union[int, List[int]] = 1) -> np.ndarray:
        """
        Resamples the given source GeoTIFF to the master grid.

        Args:
            src_path: Path to the source GeoTIFF file.
            bands: Single band index or list of band indices to read.

        Returns:
            NumPy array of the resampled data.
        """
        dst_shape: Union[Tuple[int, int], Tuple[int, int, int]]
        if isinstance(bands, int):
            band_count = 1
            dst_shape = (self.height, self.width)
        else:
            band_count = len(bands)
            dst_shape = (band_count, self.height, self.width)
            
        with rasterio.open(src_path) as src:
            destination = np.zeros(dst_shape, src.dtypes[0])
            
            reproject(
                source=rasterio.band(src, bands),
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

    def compute_quality_layer(self, height_grid: Optional[np.ndarray] = None, embed_grid: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Computes a data quality score (0.0 - 1.0) for each grid cell.
        
        Scoring:
        - DEM only: 0.25
        - DEM + Embeddings: 0.75
        - DEM + OSM: 0.5
        - All: 1.0

        Args:
            height_grid: Optional elevation grid.
            embed_grid: Optional embedding grid.

        Returns:
            NumPy array (float32) of quality scores.
        """
        quality = np.zeros((self.height, self.width), dtype=np.float32)
        
        has_dem = height_grid is not None
        has_embed = embed_grid is not None
        has_osm = "highway" in self.layers or "landuse" in self.layers
        
        if has_dem:
            quality += 0.25
            
        if has_embed:
            quality += 0.5
            
        if has_osm:
            quality += 0.25
            
        return quality