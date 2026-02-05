# Deep Earth Harmonizer - Production Specification & Handoff

## 1. Project Status Assessment

### Overview
Deep Earth Harmonizer is a multi-modal geospatial data synthesizer integrating SRTM elevation, GEE satellite embeddings, and OSM vector data into Houdini.

**Current State:** Production-ready (v0.2.0)
- 171 tests passing, 96% code coverage
- GitHub Actions CI with pytest, mypy, and wheel build (Python 3.9–3.12)
- Clean mypy (22 source files, 0 errors)
- Wheel: `deep_earth-0.2.0-py3-none-any.whl`

### Implemented Functionality
- **Unified Region Context:** `RegionContext` in `region.py` consolidates bbox logic with WGS84-to-UTM transforms and tile subdivision.
- **Core Providers:**
    - `SRTMAdapter`: Fetches elevation from OpenTopography API with caching and retry.
    - `EarthEngineAdapter`: Fetches 64-band satellite embeddings. Fail-graceful design — returns `None` on errors. Supports direct download (< 10 km²) and batch export via GCS (large regions).
    - `OverpassAdapter`: Fetches roads, buildings, waterways via Overpass API. Rasterizes vectors into distance fields and binary masks.
- **Caching:** `CacheManager` v2 with ISO8601 timestamps and per-category TTL (SRTM: never, OSM: 30 days, embeddings: 365 days).
- **CLI:** `deep-earth fetch` and `deep-earth setup` subcommands. Structured JSON output with `results` and `errors` keys. `--preview FILE` flag for headless elevation visualization.
- **Harmonizer:** `FetchResult` dataclass + `process_fetch_result()` for structured error handling. Data quality scoring (1.0 = all sources, 0.25 = DEM only).
- **Preview:** Matplotlib-based visualization (elevation, PCA, biome, OSM overlay) with headless `Agg` backend support and `output_path` for file saving.
- **Houdini Integration:** `inject_heightfield()` in `geometry.py`. HDA IR in `hda_ir/deep_earth_harmonizer.json`. Node type: `mk.pv::deep_earth::1.0`.
- **Terrain Analysis:** Derived attributes — slope, aspect, curvature, roughness, TPI, TWI.

### Resolved Issues (from original spec)
- ~~Verification scripts broken~~ — Fixed in Phase 7 (imports updated to `RegionContext`).
- ~~Tests failing/hanging~~ — 171 tests passing with full offline mock infrastructure.
- ~~Stale documentation~~ — Updated in Phase 9 (QUICKSTART, CREDENTIALS, INSTALL).
- ~~EarthEngineAdapter raises exceptions~~ — Refactored in Phase 8 to return `None` (fail-graceful).
- ~~HDA packaging unverified~~ — IR matches spec, inject_heightfield tested. Full HDA load/cook requires Houdini 21.0.

## 2. Architecture

### Data Flow
```
User inputs (bbox, resolution, year)
  → RegionContext (WGS84 → UTM)
  → Three async provider adapters fetch concurrently (return_exceptions=True)
  → Harmonizer resamples all sources to common UTM grid
  → Geometry injection into Houdini heightfield or point cloud
```

### Key Design Patterns
- **Fail-graceful:** `asyncio.gather(..., return_exceptions=True)` everywhere. Each provider can fail independently. Missing data = zero-filled arrays, not crashes.
- **Coordinate flow:** User input (WGS84) → Processing (UTM, auto-detected) → Houdini (origin-centered).
- **Provider interface:** All providers extend `DataProviderAdapter` ABC with `fetch()`, `validate_credentials()`, `get_cache_key()`, `transform_to_grid()`.
- **Houdini async bridge:** `run_async()` in `async_utils.py` handles existing event loops by running in a thread pool.

## 3. Development Infrastructure

| Tool | Status |
|------|--------|
| **pytest** | 171 tests, 96% coverage, `--cov-fail-under=90` gate |
| **mypy** | Clean (22 files), `py.typed` marker, `pyproject.toml` config |
| **CI** | GitHub Actions: pytest + mypy + wheel build, Python 3.9–3.12 |
| **Packaging** | `deep_earth-0.2.0-py3-none-any.whl`, `[preview]` optional extra |

## 4. Remaining Work

### Requires Houdini 21.0 Environment
- Full HDA load/cook verification in Houdini
- Point instancing bug fix (deferred from Phase 5)
- Interactive map picker (optional enhancement)

### Nice-to-Have
- Coverage squeeze on remaining 43 lines (preview.py interactive paths, osm.py deep branches, abstract base methods)
- `planet_embeddings_v3.md` archival
