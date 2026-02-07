"""HDA Fetch Button Callback Script - executed via exec() from button callback.

Populates the cache for all enabled providers. The internal Python SOP
handles harmonization and geometry injection on its next cook.
"""
import os
import sys

# Use environment variable for project root, or discover from package installation
_deep_earth_root = os.environ.get("DEEP_EARTH_ROOT")
if _deep_earth_root:
    _paths = [
        os.path.join(_deep_earth_root, "python"),
        os.path.join(_deep_earth_root, "venv_houdini/lib/python3.11/site-packages")
    ]
    for p in _paths:
        if p not in sys.path and os.path.isdir(p):
            sys.path.insert(0, p)

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
from deep_earth.providers.local import LocalFileAdapter

node = kwargs['node']
lat_min, lat_max = node.parmTuple("lat_range").eval()
lon_min, lon_max = node.parmTuple("lon_range").eval()
resolution = node.parm("resolution").eval()
year = node.parm("year").eval()
dataset_id = node.parm("dataset_id").eval()
local_dir = node.parm("local_dir").eval()
if not local_dir:
    local_dir = None

region = RegionContext(lat_min, lat_max, lon_min, lon_max)
config = Config()
creds = CredentialsManager()
cache = CacheManager(config.cache_path)

srtm_a = SRTMAdapter(creds, cache)
gee_a = EarthEngineAdapter(creds, cache)
osm_a = OverpassAdapter(cache_dir=config.cache_path)
local_a = LocalFileAdapter(cache)

async def fetch_all():
    tasks = [
        srtm_a.fetch(region, 30),
        gee_a.fetch(region, resolution, year, dataset_id),
        osm_a.fetch(region, resolution),
    ]
    if local_dir:
        tasks.append(local_a.fetch(region, resolution, local_dir))
    return await asyncio.gather(*tasks, return_exceptions=True)

with hou.InterruptableOperation(
    "Fetching Earth Data", open_interrupt_dialog=True
):
    run_async(fetch_all())
