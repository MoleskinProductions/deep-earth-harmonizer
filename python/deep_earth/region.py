"""
Canonical Bounding Box and Coordinate Management for Deep Earth Harmonizer.
"""

import math
import pyproj
from dataclasses import dataclass
from typing import Optional, Tuple, List, Any, cast
from shapely.geometry import box, Polygon

@dataclass(frozen=True)
class RegionContext:
    """
    Consolidated representation of a geographic region.
    Handles WGS84 coordinates, UTM transformations, and tile subdivision.
    """
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    
    def __post_init__(self) -> None:
        """Validate bounding box coordinates."""
        if not (-90 <= self.lat_min <= 90) or not (-90 <= self.lat_max <= 90):
            raise ValueError(f"Invalid latitude values: {self.lat_min}, {self.lat_max}")
        if not (-180 <= self.lon_min <= 180) or not (-180 <= self.lon_max <= 180):
            raise ValueError(f"Invalid longitude values: {self.lon_min}, {self.lon_max}")
        if self.lat_min >= self.lat_max:
            raise ValueError(f"lat_min ({self.lat_min}) must be less than lat_max ({self.lat_max})")
        if self.lon_min >= self.lon_max:
            raise ValueError(f"lon_min ({self.lon_min}) must be less than lon_max ({self.lon_max})")

    @property
    def centroid_lat(self) -> float:
        """Center latitude of the region."""
        return (self.lat_min + self.lat_max) / 2
    
    @property
    def centroid_lon(self) -> float:
        """Center longitude of the region."""
        return (self.lon_min + self.lon_max) / 2

    @property
    def utm_epsg(self) -> int:
        """EPSG code for the UTM zone covering this region."""
        zone_number = int((self.centroid_lon + 180) / 6) + 1
        base = 32600 if self.centroid_lat >= 0 else 32700
        return base + zone_number

    @property
    def utm_zone(self) -> str:
        """UTM zone name (e.g., '15N')."""
        zone_number = int((self.centroid_lon + 180) / 6) + 1
        hemi = 'N' if self.centroid_lat >= 0 else 'S'
        return f"{zone_number}{hemi}"

    @property
    def transformer(self) -> pyproj.Transformer:
        """WGS84 to UTM Transformer."""
        return pyproj.Transformer.from_crs("EPSG:4326", f"EPSG:{self.utm_epsg}", always_xy=True)

    def to_utm(self, lat: float, lon: float) -> Tuple[float, float]:
        """Transforms WGS84 lat/lon to UTM Easting/Northing."""
        return cast(Tuple[float, float], self.transformer.transform(lon, lat))

    def get_utm_bbox(self) -> Tuple[float, float, float, float]:
        """Returns the bounding box in UTM coordinates (x_min, y_min, x_max, y_max)."""
        x1, y1 = self.to_utm(self.lat_min, self.lon_min)
        x2, y2 = self.to_utm(self.lat_max, self.lon_max)
        x3, y3 = self.to_utm(self.lat_min, self.lon_max)
        x4, y4 = self.to_utm(self.lat_max, self.lon_min)
        
        return (
            min(x1, x2, x3, x4),
            min(y1, y2, y3, y4),
            max(x1, x2, x3, x4),
            max(y1, y2, y3, y4)
        )

    def width_km(self) -> float:
        """Approximate width in kilometers at center latitude."""
        lat_rad = math.radians(self.centroid_lat)
        km_per_deg = 111.32 * math.cos(lat_rad)
        return (self.lon_max - self.lon_min) * km_per_deg
    
    def height_km(self) -> float:
        """Approximate height in kilometers."""
        return (self.lat_max - self.lat_min) * 111.32
    
    def area_km2(self) -> float:
        """Approximate area in square kilometers."""
        return self.width_km() * self.height_km()

    def as_tuple(self) -> Tuple[float, float, float, float]:
        """Return as (lat_min, lon_min, lat_max, lon_max)."""
        return (self.lat_min, self.lon_min, self.lat_max, self.lon_max)

    def get_tiles(self, tile_size_km: float = 1.0) -> List['RegionContext']:
        """
        Subdivides the region into smaller tiles.
        
        Args:
            tile_size_km: Approximate target size for each tile in kilometers.
            
        Returns:
            List of RegionContext objects.
        """
        # Simple subdivision based on lat/lon degrees
        # (Assuming 111km per degree for latitude)
        lat_step = tile_size_km / 111.32
        
        # Longitude degree width varies by latitude
        lon_step = tile_size_km / (111.32 * math.cos(math.radians(self.centroid_lat)))
        
        tiles: List[RegionContext] = []
        
        curr_lat = self.lat_min
        while curr_lat < self.lat_max:
            next_lat = min(curr_lat + lat_step, self.lat_max)
            
            curr_lon = self.lon_min
            while curr_lon < self.lon_max:
                next_lon = min(curr_lon + lon_step, self.lon_max)
                
                tiles.append(RegionContext(curr_lat, next_lat, curr_lon, next_lon))
                curr_lon += lon_step
                
            curr_lat += lat_step
            
        return tiles

# Backward compatibility aliases
BoundingBox = RegionContext
CoordinateManager = RegionContext
