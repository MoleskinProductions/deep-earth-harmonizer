# Developer Experience - Specification

## CLI Interface

### Usage
```bash
python -m deep_earth [OPTIONS]
```

### Options
| Option | Type | Description |
|--------|------|-------------|
| `--bbox` | str | lat_min,lon_min,lat_max,lon_max |
| `--resolution` | float | Meters per pixel (default: 10) |
| `--year` | int | Embedding year (default: 2023) |
| `--output-dir` | path | Output directory |
| `--fetch-all` | flag | Fetch SRTM + Embeddings + OSM |

### Output
```json
{
  "srtm": "/path/to/cache/srtm_....tif",
  "embeddings": "/path/to/cache/gee_....tif",
  "osm": "/path/to/cache/osm_....json"
}
```

---

## Visualization Modes

| Mode | Description |
|------|-------------|
| `elevation` | Grayscale height map |
| `pca` | RGB from first 3 PCA components of embeddings |
| `osm` | Road/water overlay on elevation |

---

## Type Checking

Target: Zero mypy errors in strict mode.

```bash
mypy python/deep_earth --strict --ignore-missing-imports
```
