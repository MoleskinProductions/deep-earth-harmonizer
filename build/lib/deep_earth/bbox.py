"""
Unified BoundingBox representation for all data providers.
"""

from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class BoundingBox:
    """
    Geographic bounding box in WGS84 coordinates.
    
    All data providers should accept this type for their fetch() methods
    to ensure consistent coordinate handling.
    """
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    
    # Cached UTM values (computed on first access)
    _utm_epsg: Optional[int] = None
    
    def __post_init__(self):
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
        """Center latitude of the bounding box."""
        return (self.lat_min + self.lat_max) / 2
    
    @property
    def centroid_lon(self) -> float:
        """Center longitude of the bounding box."""
        return (self.lon_min + self.lon_max) / 2
    
    @property
    def utm_epsg(self) -> int:
        """EPSG code for the UTM zone covering this bounding box."""
        if self._utm_epsg is None:
            zone_number = int((self.centroid_lon + 180) / 6) + 1
            base = 32600 if self.centroid_lat >= 0 else 32700
            object.__setattr__(self, '_utm_epsg', base + zone_number)
        return self._utm_epsg
    
    @property
    def utm_zone(self) -> str:
        """UTM zone name (e.g., '15N')."""
        zone_number = int((self.centroid_lon + 180) / 6) + 1
        hemi = 'N' if self.centroid_lat >= 0 else 'S'
        return f"{zone_number}{hemi}"
    
    def as_tuple(self) -> tuple[float, float, float, float]:
        """Return as (lat_min, lon_min, lat_max, lon_max) tuple for Overpass API."""
        return (self.lat_min, self.lon_min, self.lat_max, self.lon_max)
    
    def as_wsen(self) -> tuple[float, float, float, float]:
        """Return as (west, south, east, north) / (lon_min, lat_min, lon_max, lat_max)."""
        return (self.lon_min, self.lat_min, self.lon_max, self.lat_max)
    
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
