# Deep Earth Harmonizer HDA Shell Specification

The HDA will be created manually in Houdini following this specification. 
Since we cannot automate HDA binary creation here, we will document its required parameters and internal Python logic.

## Node Type: `deep_earth_harmonizer` (SOP)

### Parameters:
| Name | Label | Type | Default |
|------|-------|------|---------|
| `lat_range` | Latitude Range | Float[2] | 44.97, 44.98 |
| `lon_range` | Longitude Range | Float[2] | -93.27, -93.26 |
| `resolution` | Master Resolution (m) | Float | 10.0 |
| `year` | Embedding Year | Int | 2023 |
| `fetch` | Fetch Data | Button | |
| `cache_path` | Cache Path | String | $HOUDINI_USER_PREF_DIR/deep_earth_cache |

### Internal Python SOP Logic (Draft):
```python
import asyncio
import hou
from deep_earth.credentials import CredentialsManager
from deep_earth.cache import CacheManager
from deep_earth.config import Config
from deep_earth.coordinates import CoordinateManager
from deep_earth.providers.srtm import SRTMAdapter
from deep_earth.providers.earth_engine import EarthEngineAdapter
from deep_earth.harmonize import Harmonizer
from deep_earth.houdini.geometry import inject_heightfield

def run_fetch(node):
    lat_min, lat_max = node.parmTuple("lat_range").eval()
    lon_min, lon_max = node.parmTuple("lon_range").eval()
    resolution = node.parm("resolution").eval()
    year = node.parm("year").eval()
    
    cm = CoordinateManager(lat_min, lat_max, lon_min, lon_max)
    config = Config()
    creds = CredentialsManager()
    cache = CacheManager(config.cache_path)
    
    srtm_adapter = SRTMAdapter(creds, cache)
    gee_adapter = EarthEngineAdapter(creds, cache)
    harmonizer = Harmonizer(cm, resolution)
    
    # Run async fetch
    loop = asyncio.get_event_loop()
    srtm_path = loop.run_until_complete(srtm_adapter.fetch(cm, 30))
    gee_path = loop.run_until_complete(gee_adapter.fetch(cm, resolution, year))
    
    # Resample
    height_grid = harmonizer.resample(srtm_path, bands=1)
    embed_grid = harmonizer.resample(gee_path, bands=list(range(1, 65)))
    
    # Inject into Houdini Geometry
    geo = node.geometry()
    inject_heightfield(geo, cm, harmonizer, height_grid, embed_grid)

# Triggered by 'fetch' button
```
