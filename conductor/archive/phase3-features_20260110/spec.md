# Feature Completion - Specification

## Hyper-Point Attributes

| Attribute | Type | Source |
|-----------|------|--------|
| `v@P` | vector3 | UTM grid transform |
| `f[]@embedding` | float[64] | GEE embeddings |
| `f@height` | float | DEM elevation |
| `f@slope` | float | Computed (degrees) |
| `f@aspect` | float | Computed (0-360°) |
| `s@highway` | string | OSM |
| `f@road_distance` | float | OSM rasterization |
| `f@water_distance` | float | OSM rasterization |
| `i@landuse_id` | int | OSM categorical |
| `f@data_quality` | float | Computed (0-1) |

---

## Terrain Analysis Formulas

### Slope
```python
dx = sobel(dem, axis=1) / (8 * cell_size)
dy = sobel(dem, axis=0) / (8 * cell_size)
slope = degrees(arctan(sqrt(dx**2 + dy**2)))
```

### Aspect
```python
aspect = degrees(arctan2(-dy, dx))
aspect = where(aspect < 0, aspect + 360, aspect)
```

---

## Data Quality Scoring

| Sources Available | Score |
|------------------|-------|
| All (DEM + Embeddings + OSM) | 1.0 |
| DEM + Embeddings | 0.75 |
| DEM + OSM | 0.5 |
| DEM only | 0.25 |
| Interpolated | 0.0 |
