import math
import pyproj
from shapely.geometry import box

class CoordinateManager:
    def __init__(self, lat_min, lat_max, lon_min, lon_max):
        self._validate_bbox(lat_min, lat_max, lon_min, lon_max)
        self.lat_min = lat_min
        self.lat_max = lat_max
        self.lon_min = lon_min
        self.lon_max = lon_max
        
        self.centroid_lat = (lat_min + lat_max) / 2
        self.centroid_lon = (lon_min + lon_max) / 2
        
        self.utm_epsg = self._get_utm_epsg(self.centroid_lat, self.centroid_lon)
        self.utm_zone = self._get_utm_zone_name(self.centroid_lon, self.centroid_lat)
        
        self.wgs84_to_utm = pyproj.Transformer.from_crs("EPSG:4326", f"EPSG:{self.utm_epsg}", always_xy=True)
        
    def _validate_bbox(self, lat_min, lat_max, lon_min, lon_max):
        if not (-90 <= lat_min <= 90) or not (-90 <= lat_max <= 90):
            raise ValueError(f"Invalid latitude values: {lat_min}, {lat_max}")
        if not (-180 <= lon_min <= 180) or not (-180 <= lon_max <= 180):
            raise ValueError(f"Invalid longitude values: {lon_min}, {lon_max}")
        if lat_min >= lat_max:
            raise ValueError(f"lat_min ({lat_min}) must be less than lat_max ({lat_max})")
        if lon_min >= lon_max:
            raise ValueError(f"lon_min ({lon_min}) must be less than lon_max ({lon_max})")

    def _get_utm_epsg(self, lat, lon):
        """Calculates the EPSG code for the UTM zone at a given lat/lon."""
        zone_number = int((lon + 180) / 6) + 1
        # North: 32600 + zone, South: 32700 + zone
        base = 32600 if lat >= 0 else 32700
        return base + zone_number

    def _get_utm_zone_name(self, lon, lat):
        """Returns the UTM zone name (e.g., '15N')."""
        zone_number = int((lon + 180) / 6) + 1
        hemi = 'N' if lat >= 0 else 'S'
        return f"{zone_number}{hemi}"

    def to_utm(self, lat, lon):
        """Transforms WGS84 lat/lon to UTM x/y."""
        return self.wgs84_to_utm.transform(lon, lat)

    def get_utm_bbox(self):
        """Returns the bounding box in UTM coordinates (x_min, y_min, x_max, y_max)."""
        # We need to transform all corners to get the actual projected bounds
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
