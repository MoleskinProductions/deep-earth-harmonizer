# Deep Earth Harmonizer - Production Specification & Handoff

## 1. Project Status Assessment

### Overview
Deep Earth Harmonizer is a multi-modal geospatial data synthesizer integrating SRTM elevation, GEE satellite embeddings, and OSM vector data into Houdini. 

**Current State:** Beta / Foundation
- Core Python package (`deep_earth`) structure is solid.
- Key providers (SRTM, GEE, OSM) are implemented with async fetching.
- Smart caching (v2 with TTL) and Unified Region Context are implemented.
- CLI (`deep-earth`) is implemented with legacy support.
- Houdini HDA foundation exists but needs polish and verification.

### Implemented Functionality
- **Unified Region Context:** [RegionContext](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/python/deep_earth/region.py#11-131) in [region.py](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/tests/test_region.py) correctly consolidates bbox logic, replacing legacy `bbox.py` (which is missing, causing breaks in old scripts).
- **Core Providers:** 
    - `SRTMAdapter`: Implemented.
    - [EarthEngineAdapter](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/python/deep_earth/providers/earth_engine.py#21-206): Implemented with Batch Export for large regions and direct download for small ones. Includes fail-graceful logic? (Code raises RuntimeError on batch fail, so only partial).
    - [OverpassAdapter](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/python/deep_earth/providers/osm.py#22-283): Implemented with comprehensive feature extraction (roads, buildings, water).
- **Caching:** [CacheManager](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/python/deep_earth/cache.py#10-183) implements v2 metadata with ISO8601 timestamps and TTL support. [planet_embeddings_v3.md](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/planet_embeddings_v3.md) concern about this seems addressed.
- **CLI:** [cli.py](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/tests/test_cli.py) implements the "Foundation Track" requirements with [fetch](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/python/deep_earth/providers/earth_engine.py#73-111) and [setup](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/python/deep_earth/cli.py#88-95) commands.
- **Houdini Integration:** [geometry.py](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/tests/test_houdini_geometry.py) contains point injection logic, updated to use valid `createPoints` calls.

### Missing / Incomplete / Broken
- **Verification Scripts:** [verify_manual.py](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/verify_manual.py) is broken (imports `deep_earth.bbox` which does not exist).
- **Tests:** `pytest` suite exists but status is unverified (commands hanging/silent in current environment).
- **Documentation:** [planet_embeddings_v3.md](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/planet_embeddings_v3.md) contains outdated "Immediate Attention" items that have been fixed (e.g., [pyproject.toml](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/pyproject.toml) has `scipy`, [cache.py](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/tests/test_cache.py) has metadata), causing confusion.
- **HDA Distribution:** HDA binary is in `otls/` but packaging logic (ensure internal python path) needs verification.
- **Error Handling:** [EarthEngineAdapter](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/python/deep_earth/providers/earth_engine.py#21-206) raises exceptions on failures rather than returning partial results/data quality flags in some paths.

## 2. Technical Findings & Recommendations

### A. Codebase Hygiene
- **Consolidate Bbox:** The move to [RegionContext](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/python/deep_earth/region.py#11-131) is good, but consumers like [verify_manual.py](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/verify_manual.py) were left broken.
    - *Action:* Update all scripts/tests to use `from deep_earth.region import RegionContext`.
- **Remove Stale Docs:** [planet_embeddings_v3.md](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/planet_embeddings_v3.md) refers to fixed issues.
    - *Action:* Archive or update this file to reflect current state.

### B. Validation Results
- **Run Manual:** FAILED. `ModuleNotFoundError: No module named 'deep_earth.bbox'`.
- **Automated Tests:** Status Unknown (Time out). Environment likely lacks credentials or network access for live tests.
    - *Recommendation:* Mock network calls in tests to allow offline verification.

### C. Architecture
- **Fail-Graceful:** The goal is non-blocking pipelines. Current adapters still raise exceptions (e.g. `RuntimeError` in GEE batch).
    - *Action:* Refactor [fetch](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/python/deep_earth/providers/earth_engine.py#73-111) methods to return a `Result` object or similar, or ensure `return_exceptions=True` in `asyncio.gather` is handled correctly by *all* callers (CLI handles it, but check HDA).

## 3. Work Plan (Next Steps)

### Phase 1: Repair & Validate (High Priority)
1.  **Fix Verification Script:** Update [verify_manual.py](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/verify_manual.py) to import [RegionContext](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/python/deep_earth/region.py#11-131) from `deep_earth.region`.
2.  **Verify Tests:** Run `pytest` with verbose output and/or mock credentials to ensure a clean baseline.
3.  **Update Deps:** Verify [pyproject.toml](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/pyproject.toml) dependencies effectively install in the target environment.

### Phase 2: HDA & Feature Polish
1.  **HDA Integration:** Verify `sop_mk.pv.deep_earth.1.0.hdalc` correctly calls the updated `deep_earth` package.
2.  **Robust Error Handling:** Modify [EarthEngineAdapter](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/python/deep_earth/providers/earth_engine.py#21-206) to log errors and return `None` (or failure object) instead of crashing, allowing partial data harmonization.
3.  **Visualization:** Ensure [preview.py](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/tests/test_preview.py) works for headless debugging (Matplotlib).

### Phase 3: Documentation & Release
1.  **Clean Documentation:** specific HDA install guide.
2.  **Package:** Build final wheel and HDA.

## 4. Immediate Action Items for Coding Agents
- [ ] **Refactor:** Modify [verify_manual.py](file:///home/frank-martinelli/pixel_vision/deep-earth-harmonizer/verify_manual.py) to fix imports.
- [ ] **Test:** Run/Fix unit tests in `tests/`.
- [ ] **Feature:** Implement "Partial Success" support in `Harmonizer` (handle missing GEE/SRTM layers gracefully).
