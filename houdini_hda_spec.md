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
| `fetch` | Fetch Data | Button | |
| `cache_path` | Cache Path | String | $HOUDINI_USER_PREF_DIR/deep_earth_cache |

---

## HDA Python Module (`hou.phm()`)
Used for the `fetch` button callback.

The fetch button uses a callback script that accesses the node via `kwargs['node']`.
This pattern is standard for HDA button callbacks.

```python
# Button callback script (executed via exec())
# Note: kwargs['node'] provides the HDA node reference

import hou
import asyncio
from deep_earth.async_utils import run_async
from deep_earth.credentials import CredentialsManager
from deep_earth.cache import CacheManager
from deep_earth.config import Config
from deep_earth.region import RegionContext
from deep_earth.providers.srtm import SRTMAdapter
from deep_earth.providers.earth_engine import EarthEngineAdapter
from deep_earth.providers.osm import OverpassAdapter

node = kwargs['node']  # HDA node reference from button callback
lat_min, lat_max = node.parmTuple("lat_range").eval()
lon_min, lon_max = node.parmTuple("lon_range").eval()
resolution = node.parm("resolution").eval()
year = node.parm("year").eval()

region = RegionContext(lat_min, lat_max, lon_min, lon_max)
config = Config()
creds = CredentialsManager()
cache = CacheManager(config.cache_path)

srtm_a = SRTMAdapter(creds, cache)
gee_a = EarthEngineAdapter(creds, cache)
osm_a = OverpassAdapter(cache_dir=config.cache_path)

async def fetch_all():
    return await asyncio.gather(
        srtm_a.fetch(region, 30),
        gee_a.fetch(region, resolution, year),
        osm_a.fetch(region, resolution),
        return_exceptions=True
    )

with hou.InterruptableOperation("Fetching Earth Data", open_interrupt_dialog=True):
    run_async(fetch_all())

# Force cook the internal Python SOP to update geometry
node.node("python1").cook(force=True)
```

---

## Internal Python SOP (`python1`)
This node lives inside the HDA subnet and performs the harmonization and geometry injection.
The node is named `python1` (Houdini's default naming for Python SOPs).

```python
import hou
import asyncio
import numpy as np
import logging
from deep_earth.async_utils import run_async
from deep_earth.region import RegionContext
from deep_earth.harmonize import Harmonizer
from deep_earth.houdini.geometry import inject_heightfield
from deep_earth.providers.srtm import SRTMAdapter
from deep_earth.providers.earth_engine import EarthEngineAdapter
from deep_earth.providers.osm import OverpassAdapter
from deep_earth.credentials import CredentialsManager
from deep_earth.cache import CacheManager
from deep_earth.config import Config

logger = logging.getLogger("deep_earth.hda")


node = hou.pwd()
hda = node.parent()

# 1. Setup Context
lat_min, lat_max = hda.parmTuple("lat_range").eval()
lon_min, lon_max = hda.parmTuple("lon_range").eval()
res = hda.parm("resolution").eval()
year = hda.parm("year").eval()
# Use evalAsString() for more robust menu handling
viz_mode_str = hda.parm("viz_mode").evalAsString().lower()
viz_mode = viz_mode_str if viz_mode_str != "none" else None

region = RegionContext(lat_min, lat_max, lon_min, lon_max)
harmonizer = Harmonizer(region, res)
config = Config()
cache = CacheManager(config.cache_path)
creds = CredentialsManager()

# Update Credential Status on UI
valid_map = creds.validate()
hda.setUserData("ee_status", "Valid" if valid_map["earth_engine"] else "Invalid/Missing")
hda.setUserData("ot_status", "Valid" if valid_map["opentopography"] else "Invalid/Missing")

# 2. Adapters
srtm_a = SRTMAdapter(creds, cache)
gee_a = EarthEngineAdapter(creds, cache)
osm_a = OverpassAdapter(cache_dir=config.cache_path)

# 3. Pull from Cache (Fast)
# Using return_exceptions=True to avoid crashing if one source fails
srtm_path, gee_path, osm_json = run_async(asyncio.gather(
    srtm_a.fetch(region, 30),
    gee_a.fetch(region, res, year),
    osm_a.fetch(region, res),
    return_exceptions=True
))

# 4. Harmonize (with structured result handling)
height_grid, srtm_result = harmonizer.process_fetch_result(srtm_path, "srtm", bands=1)
if height_grid is None:
    height_grid = np.zeros((harmonizer.height, harmonizer.width), dtype=np.float32)

embed_grid, gee_result = harmonizer.process_fetch_result(
    gee_path, "gee", bands=list(range(1, 65))
)
if embed_grid is None:
    embed_grid = np.zeros((64, harmonizer.height, harmonizer.width), dtype=np.float32)

if not isinstance(osm_json, Exception) and osm_json:
    osm_layers = osm_a.transform_to_grid(osm_json['elements'], harmonizer)
    harmonizer.add_layers(osm_layers)

# 5. Data Quality
quality = harmonizer.compute_quality_layer(
    height_grid if srtm_result.ok else None,
    embed_grid if gee_result.ok else None
)
harmonizer.add_layers({"data_quality": quality})

# 6. Inject Geometry
geo = node.geometry()
inject_heightfield(geo, region, harmonizer, height_grid, embed_grid, viz_mode=viz_mode)
```
