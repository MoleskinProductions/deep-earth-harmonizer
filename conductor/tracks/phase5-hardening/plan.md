# Production Hardening - Plan

## Goal
Address critical edge cases and stabilize core services for production-scale use.

## Tasks

### 5.1 Project Manifest & Dependencies
- [x] Add `scipy` to `project.dependencies` in `pyproject.toml` (0047adc)
- [x] Add `earthengine-api` if not present (verify manifest) (0047adc)
- [x] Verify wheel build under Houdini's Python 3.11 (0047adc)

### 5.2 Houdini Point Instancing Fix
- [x] Update `python/deep_earth/houdini/geometry.py` to fix `createPoints` call (8cb2180)
- [x] Use `createPoint` in a loop or `createPoints` with explicit positions (8cb2180)
- [x] Add unit test with mock `hou` to verify correct point creation calls (8cb2180)

### 5.3 Earth Engine Scaling
- [x] Refactor `EarthEngineAdapter.fetch` to use `ee.batch.Export.image.toDrive` or Cloud Storage (506b729)
- [x] Implement polling logic with exponential backoff (506b729)
- [x] Surface partial results via `f@data_quality` if some layers fail (506b729)

### 5.4 Cache Metadata Alignment
- [x] Update `CacheManager` to store ISO8601 timestamps and TTL per entry (3dee249)
- [x] Implement schema versioning in `cache_metadata.json` (3dee249)
- [x] Add migration path helper to clear stale entries (3dee249)

### 5.5 Bounding Box Consolidation
- [x] Merge `BoundingBox` and `CoordinateManager` responsibilities into a single canonical dataclass (506b729)
- [x] Standardize attribute names used for cache keys (506b729)
- [x] Update all providers to use this canonical type (506b729)

### 5.6 Adapter Hardening
- [~] Defer Earth Engine initialization until first fetch
- [ ] Ensure missing credentials do not crash the Harmonizer cook
- [ ] Add structured logging for fetch progress and failures

## Files to Modify
| Action | File |
|--------|------|
| MODIFY | `pyproject.toml` |
| MODIFY | `python/deep_earth/houdini/geometry.py` |
| MODIFY | `python/deep_earth/providers/earth_engine.py` |
| MODIFY | `python/deep_earth/cache.py` |
| MODIFY | `python/deep_earth/bbox.py` |
| MODIFY | `python/deep_earth/coordinates.py` |
| MODIFY | `python/deep_earth/providers/base.py` |

## Verification
```bash
# Verify venv works with new manifest
pip install .
# Run existing tests
pytest tests/ -v
# Scale test: Fetch 10km x 10km bbox
# (Manual) Verify in Houdini Geometry Spreadsheet
```
