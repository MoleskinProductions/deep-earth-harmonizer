import hashlib
import json
import aiohttp
import numpy as np
import pyproj
import logging
from typing import Any, Union, Dict, List, Optional, Tuple, cast
from shapely.geometry import LineString, Polygon, Point
from shapely.ops import transform
from rasterio.features import rasterize
from scipy.ndimage import distance_transform_edt

from deep_earth.region import RegionContext
from deep_earth.providers.base import DataProviderAdapter
from deep_earth.cache import CacheManager
from deep_earth.config import Config
from deep_earth.retry import fetch_with_retry

logger = logging.getLogger(__name__)


class OverpassAdapter(DataProviderAdapter):
    """
    Adapter for fetching and processing OpenStreetMap data via the Overpass API.
    """
    DEFAULT_API_URL = "https://overpass-api.de/api/interpreter"

    def __init__(self, base_url: Optional[str] = None, fallback_urls: Optional[List[str]] = None, cache_dir: Optional[str] = None):
        """
        Initialize the OverpassAdapter.

        Args:
            base_url: The base URL for the Overpass API.
            fallback_urls: List of fallback API URLs.
            cache_dir: Custom cache directory.
        """
        self.base_url = base_url or self.DEFAULT_API_URL
        self.fallback_urls = fallback_urls or []
        
        if cache_dir is None:
            config = Config()
            cache_dir = config.cache_path
        self.cache = CacheManager(cache_dir)

    def _build_query(self, bbox: Union[RegionContext, Tuple[float, float, float, float]]) -> str:
        """
        Construct an Overpass QL query for the given bounding box.
        
        Args:
            bbox: RegionContext instance or Tuple of (min_lat, min_lon, max_lat, max_lon).
            
        Returns:
            The formatted Overpass QL query string.
        """
        if isinstance(bbox, RegionContext):
            bbox_tuple = bbox.as_tuple()
        else:
            bbox_tuple = bbox
            
        min_lat, min_lon, max_lat, max_lon = bbox_tuple
        bbox_str = f"{min_lat},{min_lon},{max_lat},{max_lon}"
        
        query = f"""
        [out:json][timeout:25];
        (
          way["highway"]({bbox_str});
          way["waterway"]({bbox_str});
          way["building"]({bbox_str});
          relation["building"]({bbox_str});
          way["landuse"]({bbox_str});
          relation["landuse"]({bbox_str});
          way["natural"]({bbox_str});
          relation["natural"]({bbox_str});
        );
        out geom;
        """
        return query.strip()

    def _parse_elements(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parse Overpass JSON elements into Shapely geometries and categorized features.

        Args:
            elements: List of element dictionaries from Overpass JSON.

        Returns:
            List of parsed feature dictionaries.
        """
        features = []
        for el in elements:
            tags = el.get("tags", {})
            geom = el.get("geometry", [])
            if not geom:
                continue
            
            # Convert geometry to Shapely coords (lon, lat)
            coords = [(p["lon"], p["lat"]) for p in geom]
            
            feature_type = "unknown"
            shape = None
            
            if "highway" in tags:
                feature_type = "road"
                shape = LineString(coords)
            elif "waterway" in tags:
                feature_type = "waterway"
                shape = LineString(coords)
            elif "building" in tags:
                feature_type = "building"
                shape = Polygon(coords) if len(coords) >= 3 else Point(coords[0])
                if "height" in tags:
                    try:
                        tags["height"] = float(tags["height"])
                    except (ValueError, TypeError):
                        pass
            elif "landuse" in tags:
                feature_type = "landuse"
                shape = Polygon(coords) if len(coords) >= 3 else Point(coords[0])
            elif "natural" in tags:
                feature_type = "natural"
                shape = Polygon(coords) if len(coords) >= 3 else Point(coords[0])
            else:
                continue
            
            if shape:
                features.append({
                    "type": feature_type,
                    "geometry": shape,
                    "tags": tags,
                    "id": el.get("id")
                })
        return features

    def get_cache_key(self, bbox: Union[RegionContext, Tuple[float, float, float, float]], resolution: float) -> str:
        """Generates a unique cache key for the given parameters."""
        bbox_tuple: Tuple[float, float, float, float]
        if isinstance(bbox, RegionContext):
            bbox_tuple = bbox.as_tuple()
        else:
            bbox_tuple = bbox
        bbox_str = f"{bbox_tuple[0]},{bbox_tuple[1]},{bbox_tuple[2]},{bbox_tuple[3]}"
        return hashlib.md5(bbox_str.encode()).hexdigest()

    async def fetch(self, bbox: Union[RegionContext, Tuple[float, float, float, float]], resolution: float) -> Dict[str, Any]:
        """
        Fetch data from Overpass API.
        
        Args:
            bbox: RegionContext or tuple of (min_lat, min_lon, max_lat, max_lon).
            resolution: Requested resolution (not used for fetch, but for cache key).
            
        Returns:
            The JSON response from Overpass.
        """
        bbox_tuple: Tuple[float, float, float, float]
        if isinstance(bbox, RegionContext):
            bbox_tuple = bbox.as_tuple()
        else:
            bbox_tuple = bbox
            
        logger.info(f"Fetching OSM data for bbox {bbox_tuple}")
        key = self.get_cache_key(bbox_tuple, resolution)
        
        if self.cache.exists(key, "osm", "json"):
            logger.debug(f"Cache hit for {key}")
            path = self.cache.get_path(key, "osm", "json")
            if path:
                with open(path, "r") as f:
                    return cast(Dict[str, Any], json.load(f))

        logger.debug(f"Cache miss for {key}")
        query = self._build_query(bbox_tuple)
        
        async with aiohttp.ClientSession() as session:
            try:
                data = await fetch_with_retry(session, self.base_url, params={'data': query})
                logger.info("Fetched OSM data successfully")
                self.cache.save(key, data, "osm", "json")
                return cast(Dict[str, Any], json.loads(data))
            except Exception as e:
                logger.error(f"Failed to fetch OSM: {e}")
                raise

    def validate_credentials(self) -> bool:
        """OSM Overpass API is public."""
        return True

    def transform_to_grid(self, data: List[Dict[str, Any]], target_grid: Any) -> Dict[str, np.ndarray]:
        """
        Transforms parsed OSM features into a set of raster layers aligned with the target grid.

        Args:
            data: List of parsed feature dictionaries.
            target_grid: The Harmonizer instance providing the target grid metadata.

        Returns:
            Dictionary mapping layer names to NumPy arrays.
        """
        width, height = target_grid.width, target_grid.height
        transform_meta = target_grid.dst_transform
        
        # Prepare coordinate transformer from WGS84 to Target CRS
        wgs84 = pyproj.CRS("EPSG:4326")
        target_crs = pyproj.CRS(target_grid.dst_crs)
        project_func = pyproj.Transformer.from_crs(wgs84, target_crs, always_xy=True).transform
        
        # Initialize result layers
        layers: Dict[str, np.ndarray] = {
            "road_distance": np.full((height, width), 1e6, dtype=np.float32),
            "water_distance": np.full((height, width), 1e6, dtype=np.float32),
            "natural_distance": np.full((height, width), 1e6, dtype=np.float32),
            "building_mask": np.zeros((height, width), dtype=np.uint8),
            "building_height": np.zeros((height, width), dtype=np.float32),
            "landuse_id": np.zeros((height, width), dtype=np.int32),
            "landuse": np.full((height, width), "", dtype=object),
            "highway": np.full((height, width), "", dtype=object)
        }
        
        categorized_shapes: Dict[str, List[Any]] = {
            "road": [],
            "waterway": [],
            "building": [],
            "landuse": [],
            "natural": []
        }
        
        for feat in data:
            # Project geometry to target CRS
            projected_geom = transform(project_func, feat["geometry"])
            feat_type = feat["type"]
            if feat_type in categorized_shapes:
                categorized_shapes[feat_type].append((projected_geom, feat))

        # 0. Rasterize Highways (Strings)
        if categorized_shapes["road"]:
            highway_types = sorted(list(set(f["tags"].get("highway", "unknown") for s, f in categorized_shapes["road"])))
            type_to_id = {t: i+1 for i, t in enumerate(highway_types)}
            id_to_type = {i+1: t for i, t in enumerate(highway_types)}
            id_to_type[0] = ""
            
            hw_shapes = [(s, type_to_id.get(f["tags"].get("highway", "unknown"), 0)) for s, f in categorized_shapes["road"]]
            hw_ids = rasterize(hw_shapes, out_shape=(height, width), transform=transform_meta)
            
            v_id_to_type = np.vectorize(lambda x: id_to_type.get(x, ""))
            layers["highway"] = v_id_to_type(hw_ids).astype(object)

        # 1. Rasterize Buildings
        if categorized_shapes["building"]:
            shapes = [s for s, f in categorized_shapes["building"]]
            mask = rasterize(shapes, out_shape=(height, width), transform=transform_meta)
            layers["building_mask"] = mask
            
            height_shapes = [(s, f["tags"].get("height", 0)) for s, f in categorized_shapes["building"]]
            layers["building_height"] = rasterize(height_shapes, out_shape=(height, width), transform=transform_meta)

        # 2. Rasterize Landuse (categorical)
        if categorized_shapes["landuse"]:
            landuse_types = sorted(list(set(f["tags"].get("landuse", "unknown") for s, f in categorized_shapes["landuse"])))
            type_to_id_lu = {t: i+1 for i, t in enumerate(landuse_types)}
            id_to_type_lu = {i+1: t for i, t in enumerate(landuse_types)}
            id_to_type_lu[0] = ""
            
            lu_shapes = [(s, type_to_id_lu.get(f["tags"].get("landuse", "unknown"), 0)) for s, f in categorized_shapes["landuse"]]
            lu_ids = rasterize(lu_shapes, out_shape=(height, width), transform=transform_meta)
            layers["landuse_id"] = lu_ids
            
            v_lu_id_to_type = np.vectorize(lambda x: id_to_type_lu.get(x, ""))
            layers["landuse"] = v_lu_id_to_type(lu_ids).astype(object)

        # 3. Distance Fields (Roads, Water, Natural)
        for cat, layer_name in [("road", "road_distance"), ("waterway", "water_distance"), ("natural", "natural_distance")]:
            if categorized_shapes[cat]:
                cat_shapes = [s for s, f in categorized_shapes[cat]]
                binary_mask = rasterize(cat_shapes, out_shape=(height, width), transform=transform_meta)
                
                if np.any(binary_mask):
                    dist = distance_transform_edt(1 - binary_mask)
                    # Convert pixel distance to meters
                    pixel_size = abs(transform_meta[0]) 
                    layers[layer_name] = (dist * pixel_size).astype(np.float32)

        return layers