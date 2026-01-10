import numpy as np
import rasterio
import math
from rasterio.warp import reproject, Resampling

class Harmonizer:
    def __init__(self, coordinate_manager, resolution=10):
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
        
        self.layers = {}

    def resample(self, src_path, bands=1):
        """Resamples the given source GeoTIFF to the master grid."""
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

    def add_layers(self, layers_dict):
        """
        Adds multiple layers to the harmonizer.
        Each layer must be a NumPy array with (height, width) matching the master grid.
        """
        for name, data in layers_dict.items():
            if data.shape != (self.height, self.width):
                raise ValueError(f"Layer dimensions {data.shape} do not match master grid {(self.height, self.width)}")
            self.layers[name] = data

    def compute_quality_layer(self, height_grid=None, embed_grid=None):
        """
        Computes a data quality score (0.0 - 1.0) for each grid cell.
        
        Scoring:
        - DEM only: 0.25
        - DEM + Embeddings: 0.75
        - DEM + OSM: 0.5
        - All: 1.0
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