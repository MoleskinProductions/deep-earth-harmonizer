# Production Hardening - Specification

## Earth Engine Scaling Strategy

Large regions (>50MB payload) must use the batch export system.

| Step | Method | Description |
|------|--------|-------------|
| 1. Export | `ee.batch.Export.image.toDrive` | Start export task |
| 2. Poll | `task.status()['state']` | Check status every 5-10s |
| 3. Backoff | `tenacity` | Use exponential backoff for status checks |
| 4. Download | Signed URL / Direct Drive access | Retrieve GeoTIFF once ready |

## Canonical Bounding Box Dataclass

```python
@dataclass
class RegionContext:
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    
    # Properties
    utm_epsg: int
    utm_bbox: tuple[float, float, float, float]
    area_km2: float
    
    # Helpers
    def get_tiles(self, tile_size_m: float) -> list['RegionContext']:
        pass
```

## Cache Metadata Schema v2

```json
{
  "schema_version": 2,
  "entries": {
    "cache_key_hash": {
      "timestamp": "2026-01-10T12:00:00Z",
      "ttl_days": 30,
      "provider": "osm",
      "params": { ... }
    }
  }
}
```
