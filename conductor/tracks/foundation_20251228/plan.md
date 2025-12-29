# Track Plan: Foundation - Async Fetching and Harmonization

## Phase 1: Environment & Credentials [checkpoint: d2448ed]
- [x] Task: Set up Python package structure (`python/deep_earth/`) and basic dependencies. 96932e3
- [x] Task: Implement `credentials.py` for handling OpenTopography and GEE secrets. 37efde7
- [x] Task: Implement `config.py` for cache path and system settings. 8f5bb0d
- [x] Task: Conductor - User Manual Verification 'Environment & Credentials' (Protocol in workflow.md) d2448ed

## Phase 2: Coordinate & Data Infrastructure [checkpoint: 68ce148]
- [x] Task: Implement `coordinates.py` for UTM transformation and bounding box validation. f9e57a9
- [x] Task: Implement base `DataProviderAdapter` class in `providers/base.py`. eb52b9c
- [x] Task: Implement `cache.py` for tile-based disk caching. 312c000
- [x] Task: Conductor - User Manual Verification 'Coordinate & Data Infrastructure' (Protocol in workflow.md) 68ce148

## Phase 3: SRTM & Elevation Fetching [checkpoint: 693a8ea]
- [x] Task: Write tests for `SRTMAdapter`. 2e16780
- [x] Task: Implement `providers/srtm.py` using `aiohttp` for OpenTopography REST API. fd57e67
- [x] Task: Verify mosaic and reprojection of SRTM tiles. ea19947
- [x] Task: Conductor - User Manual Verification 'SRTM & Elevation Fetching' (Protocol in workflow.md) 693a8ea

## Phase 4: GEE Embeddings Integration [checkpoint: 74bbc2c]
- [x] Task: Write tests for `EarthEngineAdapter`. ad37b44
- [x] Task: Implement `providers/earth_engine.py` using the `earthengine-api`. 5468c83
- [x] Task: Implement async export/polling logic for GEE embeddings. cd699b8
- [x] Task: Conductor - User Manual Verification 'GEE Embeddings Integration' (Protocol in workflow.md) 74bbc2c

## Phase 5: Harmonization & Houdini SOP
- [ ] Task: Implement `harmonize.py` for grid resampling using `rasterio` and `numpy`.
- [ ] Task: Create a basic Houdini HDA shell with a Python SOP.
- [ ] Task: Implement the "Hyper-Point" attribute injection logic in `houdini/geometry.py`.
- [ ] Task: Conductor - User Manual Verification 'Harmonization & Houdini SOP' (Protocol in workflow.md)
