# Quick Start Guide

This guide walks you through fetching geospatial data for a region and using it in Houdini.

## Example: Downtown Minneapolis

We'll fetch terrain data for a small area of downtown Minneapolis.

### CLI Usage

Fetch data using the command line:

```bash
deep-earth fetch --bbox 44.97,-93.27,44.98,-93.26 --resolution 10
```

**Parameters:**
- `--bbox` - Bounding box as `lat_min,lon_min,lat_max,lon_max`
- `--resolution` - Target resolution in meters (default: 10)
- `--year` - Satellite embedding year (default: 2023)

**Expected output:**

```json
{
  "srtm": "/home/user/.deep_earth_cache/srtm_44.97_-93.27_44.98_-93.26.tif",
  "embeddings": "/home/user/.deep_earth_cache/ee_embed_44.97_-93.27_2023.tif",
  "osm": "/home/user/.deep_earth_cache/osm_44.97_-93.27_44.98_-93.26.json"
}
```

The paths point to cached data files that can be used by Houdini or other tools.

## Houdini HDA Workflow

### 1. Create the Node

1. Open Houdini
2. Create a Geometry node at `/obj` level
3. Dive inside and Tab-search for **"Deep Earth Harmonizer"**
4. Place the node

### 2. Set Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Latitude Range | 44.97, 44.98 | South/North bounds |
| Longitude Range | -93.27, -93.26 | West/East bounds |
| Resolution | 10.0 | Meters per pixel |
| Year | 2024 | Satellite data year |

### 3. Fetch Data

Click the **Fetch Data** button. This will:

1. Download SRTM elevation data (30m)
2. Fetch Earth Engine satellite embeddings
3. Query OpenStreetMap for vector features
4. Cache all results locally

A progress dialog shows the fetch status.

### 4. View Results

After fetching, the node outputs a heightfield with:

**Volume Layers:**
- `height` - Elevation in meters
- `embed_0` through `embed_63` - 64-band satellite embeddings
- `road_distance` - Distance to nearest road
- `building_mask` - Building footprint coverage
- `water_mask` - Water body coverage
- `data_quality` - Confidence score (0-1)

**Visualization Modes:**
- **None** - Raw height visualization
- **PCA** - 3-band PCA of embeddings mapped to Cd
- **Biome** - K-means clustering visualization

### 5. Use in Your Network

Connect the Deep Earth output to:

- **HeightField Erode** - Add erosion detail
- **HeightField Scatter** - Place vegetation points
- **HeightField Mask** - Create masks from layers

## Output Attributes

The heightfield geometry includes point attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `height` | float | Elevation value |
| `embed` | float[64] | ML embedding vector |
| `road_dist` | float | Distance to road (meters) |
| `building` | float | Building coverage (0-1) |
| `water` | float | Water coverage (0-1) |
| `quality` | float | Data quality score |

When visualization is enabled:

| Attribute | Type | Description |
|-----------|------|-------------|
| `Cd` | vector3 | Color from PCA or biome |
| `biome_id` | int | Cluster assignment (biome mode) |

## Larger Regions

For production-scale terrain:

```bash
# 10km x 10km region at 30m resolution
deep-earth fetch --bbox 44.9,-93.3,45.0,-93.2 --resolution 30
```

Tips for large fetches:
- Use coarser resolution (30m) to reduce data size
- Earth Engine may timeout for very large regions
- Results are cached, so subsequent fetches are fast

## Next Steps

- Explore the cached GeoTIFF files with QGIS or rasterio
- Use the embeddings for ML-based terrain classification
- Build procedural systems driven by real-world data

See [CREDENTIALS.md](CREDENTIALS.md) if you encounter authentication errors.
