# Deep Earth Harmonizer HDA Shell Specification (Houdini 21.0)

The HDA is created manually in Houdini following this specification. It uses a split architecture: fetching logic in the HDA Python Module (Scripts tab) and geometry generation in an internal Python SOP.

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

```python
import hou
from deep_earth.async_utils import run_async
from deep_earth.credentials import CredentialsManager
from deep_earth.cache import CacheManager
from deep_earth.config import Config
from deep_earth.region import RegionContext
from deep_earth.providers.srtm import SRTMAdapter
from deep_earth.providers.earth_engine import EarthEngineAdapter
from deep_earth.providers.osm import OverpassAdapter

async def fetch_all_data(srtm_adapter, gee_adapter, osm_adapter, region, resolution, year):
    """Fetch all data sources concurrently."""
    import asyncio
    # Use return_exceptions=True so one failure doesn't block others
    results = await asyncio.gather(
        srtm_adapter.fetch(region, 30),
        gee_adapter.fetch(region, resolution, year),
        osm_adapter.fetch(region, resolution),
        return_exceptions=True
    )
    return results

def run_fetch(node):
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
    
    with hou.InterruptableOperation("Fetching Earth Data", open_interrupt_dialog=True) as op:
        run_async(fetch_all_data(srtm_a, gee_a, osm_a, region, resolution, year))
    
    # Force cook the internal python SOP to update geometry
    node.node("python_injection").cook(force=True)
```

---

## Internal Python SOP (`python_injection`)
This node lives inside the HDA subnet and performs the harmonization and geometry injection.

```python
import hou
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

# 4. Harmonize (with error guards)
if not isinstance(srtm_path, Exception) and srtm_path:
    height_grid = harmonizer.resample(srtm_path, bands=1)
else:
    height_grid = np.zeros((harmonizer.height, harmonizer.width), dtype=np.float32)
    logger.error(f"SRTM failed: {srtm_path}")

if not isinstance(gee_path, Exception) and gee_path:
    embed_grid = harmonizer.resample(gee_path, bands=list(range(1, 65)))
else:
    embed_grid = np.zeros((64, harmonizer.height, harmonizer.width), dtype=np.float32)
    logger.error(f"GEE failed: {gee_path}")

if not isinstance(osm_json, Exception) and osm_json:
    osm_layers = osm_a.transform_to_grid(osm_json['elements'], harmonizer)
    harmonizer.add_layers(osm_layers)

# 5. Data Quality
quality = harmonizer.compute_quality_layer(
    height_grid if not isinstance(srtm_path, Exception) else None, 
    embed_grid if not isinstance(gee_path, Exception) else None
)
harmonizer.add_layers({"data_quality": quality})

# 6. Inject Geometry
geo = node.geometry()
inject_heightfield(geo, region, harmonizer, height_grid, embed_grid, viz_mode=viz_mode)
```
