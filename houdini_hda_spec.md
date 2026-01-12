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
from deep_earth.coordinates import CoordinateManager
from deep_earth.providers.srtm import SRTMAdapter
from deep_earth.providers.earth_engine import EarthEngineAdapter
from deep_earth.providers.osm import OverpassAdapter

async def fetch_all_data(srtm_adapter, gee_adapter, osm_adapter, cm, resolution, year):
    """Fetch all data sources concurrently."""
    import asyncio
    # Use return_exceptions=True so one failure doesn't block others
    results = await asyncio.gather(
        srtm_adapter.fetch(cm, 30),
        gee_adapter.fetch(cm, resolution, year),
        osm_adapter.fetch(cm, resolution),
        return_exceptions=True
    )
    return results

def run_fetch(node):
    lat_min, lat_max = node.parmTuple("lat_range").eval()
    lon_min, lon_max = node.parmTuple("lon_range").eval()
    resolution = node.parm("resolution").eval()
    year = node.parm("year").eval()
    
    cm = CoordinateManager(lat_min, lat_max, lon_min, lon_max)
    config = Config()
    creds = CredentialsManager()
    cache = CacheManager(config.cache_path)
    
    srtm_a = SRTMAdapter(creds, cache)
    gee_a = EarthEngineAdapter(creds, cache)
    osm_a = OverpassAdapter(cache_dir=config.cache_path)
    
    with hou.InterruptableOperation("Fetching Earth Data", open_interrupt_dialog=True) as op:
        run_async(fetch_all_data(srtm_a, gee_a, osm_a, cm, resolution, year))
    
    # Force cook the internal python SOP to update geometry
    node.node("python_injection").cook(force=True)
```

---

## Internal Python SOP (`python_injection`)
This node lives inside the HDA subnet and performs the harmonization and geometry injection.

```python
import hou
from deep_earth.async_utils import run_async
from deep_earth.coordinates import CoordinateManager
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
viz_idx = hda.parm("viz_mode").eval()
viz_mode = hda.parm("viz_mode").menuItems()[viz_idx].lower() if viz_idx > 0 else None

cm = CoordinateManager(lat_min, lat_max, lon_min, lon_max)
harmonizer = Harmonizer(cm, res)
config = Config()
cache = CacheManager(config.cache_path)
creds = CredentialsManager()

# 2. Adapters
srtm_a = SRTMAdapter(creds, cache)
gee_a = EarthEngineAdapter(creds, cache)
osm_a = OverpassAdapter(cache_dir=config.cache_path)

# 3. Pull from Cache (Fast)
srtm_path = run_async(srtm_a.fetch(cm, 30))
gee_path = run_async(gee_a.fetch(cm, res, year))
osm_json = run_async(osm_a.fetch(cm, res))

# 4. Harmonize
height_grid = harmonizer.resample(srtm_path, bands=1)
embed_grid = harmonizer.resample(gee_path, bands=list(range(1, 65)))
osm_layers = osm_a.transform_to_grid(osm_json['elements'], harmonizer)
harmonizer.add_layers(osm_layers)

# 5. Data Quality
quality = harmonizer.compute_quality_layer(height_grid, embed_grid)
harmonizer.add_layers({"data_quality": quality})

# 6. Inject Geometry
geo = node.geometry()
inject_heightfield(geo, cm, harmonizer, height_grid, embed_grid, viz_mode=viz_mode)
```
