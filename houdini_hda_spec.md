# Deep Earth Harmonizer HDA Shell Specification (Houdini 21.0)

## Installation & Studio Deployment

### 1. Requirements
- Houdini 21.0+
- Python 3.11 (Hython)
- Python packages: `pyproj`, `shapely`, `rasterio`, `numpy`, `scikit-learn`, `earthengine-api`

### 2. Environment Setup (Recommended)
Create `~/houdini21.0/packages/deep_earth.json`:
```json
{
    "env": [
        {
            "DEEP_EARTH_ROOT": "/path/to/planet_embeddings"
        },
        {
            "PYTHONPATH": {
                "value": ["$DEEP_EARTH_ROOT/python"],
                "method": "prepend"
            }
        },
        {
            "DEEP_EARTH_GEE_SERVICE_ACCOUNT": "your@email.com",
            "DEEP_EARTH_GEE_KEY_PATH": "/path/to/key.json",
            "DEEP_EARTH_OPENTOPO_KEY": "your_api_key"
        }
    ],
    "hpath": "$DEEP_EARTH_ROOT"
}
```

See `planet_embeddings.json.template` for a distributable template.

### 3. Asset Versioning
The HDA is saved as `otls/sop_mk.pv.deep_earth.1.0.hdalc`.
Inside Houdini, the node type name is `mk.pv::deep_earth::1.0`.

---

## Node Type: `deep_earth_harmonizer` (SOP)

### Parameters:
| Name | Label | Type | Default |
|------|-------|------|---------|
| `lat_range` | Latitude Range | Float[2] | 44.97, 44.98 |
| `lon_range` | Longitude Range | Float[2] | -93.27, -93.26 |
| `resolution` | Master Resolution (m) | Float | 10.0 |
| `year` | Embedding Year | Int | 2024 |
| `viz_mode` | Visualization Mode | Menu | None, PCA, Biome |
| `dataset_id` | GEE Dataset ID | String | GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL |
| `local_dir` | Local Raster Dir | String | (empty) |
| `fetch` | Fetch Data | Button | |
| `cache_path` | Cache Path | String | $HOUDINI_USER_PREF_DIR/deep_earth_cache |

---

## HDA Python Module (`hou.phm()`)
Used for the `fetch` button callback.

The fetch button uses a callback script that accesses the node via `kwargs['node']`.
This pattern is standard for HDA button callbacks. The button **only populates the
cache** — the internal Python SOP handles harmonization and geometry injection on cook.

See `scripts/hda_fetch.py` for the full callback implementation.

---

## Internal Python SOP (`python1`)
This node lives inside the HDA subnet and performs the harmonization and geometry
injection. The node is named `python1` (Houdini's default naming for Python SOPs).

**Output:** A point cloud (not a heightfield volume). One point per grid cell with:
- Position: X = UTM Easting, Y = Elevation, Z = UTM Northing
- `height` (float) — elevation value (mirrors Y position)
- `embedding` (float[64]) — satellite embedding bands
- OSM layers as float/int/string point attributes
- `data_quality` (float) — composite quality score
- `Cd` (float[3]) — color, if visualization mode is enabled

The canonical source for this code is the HDA IR JSON at
`hda_ir/deep_earth_harmonizer.json`.
