# Track Plan: Foundation - Async Fetching and Harmonization

## Phase 1: Environment & Credentials
- [x] Task: Set up Python package structure (`python/deep_earth/`) and basic dependencies. 96932e3
- [ ] Task: Implement `credentials.py` for handling OpenTopography and GEE secrets.
- [ ] Task: Implement `config.py` for cache path and system settings.
- [ ] Task: Conductor - User Manual Verification 'Environment & Credentials' (Protocol in workflow.md)

## Phase 2: Coordinate & Data Infrastructure
- [ ] Task: Implement `coordinates.py` for UTM transformation and bounding box validation.
- [ ] Task: Implement base `DataProviderAdapter` class in `providers/base.py`.
- [ ] Task: Implement `cache.py` for tile-based disk caching.
- [ ] Task: Conductor - User Manual Verification 'Coordinate & Data Infrastructure' (Protocol in workflow.md)

## Phase 3: SRTM & Elevation Fetching
- [ ] Task: Write tests for `SRTMAdapter`.
- [ ] Task: Implement `providers/srtm.py` using `aiohttp` for OpenTopography REST API.
- [ ] Task: Verify mosaic and reprojection of SRTM tiles.
- [ ] Task: Conductor - User Manual Verification 'SRTM & Elevation Fetching' (Protocol in workflow.md)

## Phase 4: GEE Embeddings Integration
- [ ] Task: Write tests for `EarthEngineAdapter`.
- [ ] Task: Implement `providers/earth_engine.py` using the `earthengine-api`.
- [ ] Task: Implement async export/polling logic for GEE embeddings.
- [ ] Task: Conductor - User Manual Verification 'GEE Embeddings Integration' (Protocol in workflow.md)

## Phase 5: Harmonization & Houdini SOP
- [ ] Task: Implement `harmonize.py` for grid resampling using `rasterio` and `numpy`.
- [ ] Task: Create a basic Houdini HDA shell with a Python SOP.
- [ ] Task: Implement the "Hyper-Point" attribute injection logic in `houdini/geometry.py`.
- [ ] Task: Conductor - User Manual Verification 'Harmonization & Houdini SOP' (Protocol in workflow.md)
