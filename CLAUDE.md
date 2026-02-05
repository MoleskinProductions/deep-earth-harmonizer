# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Deep Earth Harmonizer is a multi-modal geospatial data synthesizer that fetches SRTM elevation, Google Earth Engine satellite embeddings (64-band), and OpenStreetMap vector data, harmonizes them to a common UTM grid, and injects the result as Houdini heightfield geometry with rich per-point attributes ("Hyper-Points"). It ships as both a standalone Python package (`deep_earth`) and a Houdini HDA wrapper.

## Build & Development Commands

```bash
# Install in development mode (from repo root)
pip install -e .

# Run the CLI
deep-earth fetch --bbox 44.97,-93.27,44.98,-93.26 --resolution 10
deep-earth setup

# Run all tests
pytest

# Run a single test file
pytest tests/test_harmonize.py

# Run a single test function
pytest tests/test_harmonize.py::test_function_name

# Run tests with coverage
pytest --cov=deep_earth --cov-report=html

# Module-level execution
python -m deep_earth
```

## Key Configuration

- **Python path**: `pyproject.toml` sets `[tool.setuptools.packages.find] where = ["python"]` -- all package code lives under `python/deep_earth/`, not at the repo root.
- **pytest**: configured in `pyproject.toml` with `pythonpath = ["python"]`, `asyncio_mode = "auto"`, and `testpaths = ["tests"]`.
- **Two virtualenvs exist**: `venv/` (Python 3.12, primary dev) and `venv_houdini/` (Python 3.11, matches Houdini 21.0).

## Architecture

### Data Flow

User inputs (bbox, resolution, year) -> `RegionContext` (WGS84 -> UTM) -> three async provider adapters fetch concurrently -> `Harmonizer` resamples all sources to a common UTM grid -> geometry injection into Houdini heightfield or point cloud.

### Core Modules (`python/deep_earth/`)

- **`region.py`** - `RegionContext` (frozen dataclass): canonical bbox representation, WGS84-to-UTM transforms, tile subdivision. Replaces legacy `bbox.py`. Aliases `BoundingBox` and `CoordinateManager` exist for backward compat.
- **`harmonize.py`** - `Harmonizer`: takes a `RegionContext` + resolution, computes a master UTM grid, resamples GeoTIFFs via rasterio, manages named layers, computes data quality scores.
- **`providers/base.py`** - `DataProviderAdapter` ABC with `fetch()`, `validate_credentials()`, `get_cache_key()`, `transform_to_grid()`.
- **`providers/srtm.py`** - `SRTMAdapter`: fetches elevation from OpenTopography API.
- **`providers/earth_engine.py`** - `EarthEngineAdapter`: fetches 64-band satellite embeddings from GEE. Uses batch export for large regions, direct download for small ones.
- **`providers/osm.py`** - `OverpassAdapter`: fetches roads, buildings, waterways via Overpass API. Rasterizes vectors into distance fields and binary masks.
- **`cache.py`** - `CacheManager`: v2 metadata with ISO8601 timestamps and TTL support.
- **`config.py`** - `Config`: cache path resolution (defaults to `$HOUDINI_USER_PREF_DIR/deep_earth_cache`).
- **`credentials.py`** - `CredentialsManager`: manages GEE service account and OpenTopography API key credentials.
- **`async_utils.py`** - `run_async()`: bridges async coroutines into synchronous contexts (handles Houdini's existing event loop by running in a thread pool).
- **`cli.py`** - CLI entry point with `fetch` and `setup` subcommands. Uses `asyncio.gather` with `return_exceptions=True` for fail-graceful behavior.
- **`retry.py`** - Retry logic with exponential backoff (tenacity).
- **`preview.py`** - Matplotlib-based standalone 2D visualization for debugging without Houdini.
- **`terrain_analysis.py`** - Derived attribute computation (slope, aspect, curvature, roughness, TPI, TWI).

### Houdini Integration (`python/deep_earth/houdini/`)

- **`geometry.py`** - `inject_heightfield()`: creates Houdini heightfield geometry, injects elevation/embedding/OSM layers as volumes and point attributes.
- **`visualization.py`** - Viewport visualization modes (PCA, Biome coloring).

### HDA & Scripts

- **`otls/sop_mk.pv.deep_earth.1.0.hdalc`** - The compiled Houdini Digital Asset. Node type: `mk.pv::deep_earth::1.0`.
- **`hda_ir/deep_earth_harmonizer.json`** - HouGraph IR: JSON representation of the HDA structure for version control and code-driven HDA rebuilds.
- **`scripts/hda_fetch.py`** - Button callback script used by the HDA's "Fetch Data" button.
- **`scripts/deep_earth_pdg_tile.py`** - PDG tile processor for large-region parallel fetching via hython.
- **`scripts/deep_earth_setup.py`** - First-run setup wizard.
- **`houdini_hda_spec.md`** - Detailed HDA parameter and internal node specification.

### Conductor System (`conductor/`)

Project management framework used to track development phases. All 6 tracks (Critical Fixes through Advanced Houdini & PDG) are marked complete.

- **`tracks.md`** - Master track list with completion status.
- **`product.md`** - Full product specification including architecture diagrams, Hyper-Point attribute schema, and implementation roadmap.
- **`workflow.md`** - Development workflow (TDD, commit conventions, phase checkpointing).
- **`code_styleguides/python.md`** - Google Python Style Guide conventions: 80-char lines, 4-space indent, type annotations on public APIs, Google-style docstrings with `Args:`, `Returns:`, `Raises:`.

## Important Patterns

- **Fail-graceful design**: `asyncio.gather(..., return_exceptions=True)` is used everywhere. Each provider failure is logged and handled independently -- missing data results in zero-filled arrays, not crashes. Check `isinstance(result, Exception)` before using results.
- **Coordinate flow**: All user input is WGS84 lat/lon. Internal processing uses UTM (auto-detected zone from bbox centroid). Houdini output is centered at origin.
- **Provider interface**: All providers extend `DataProviderAdapter` ABC. Adding a new data source means implementing `fetch()`, `validate_credentials()`, `get_cache_key()`, and `transform_to_grid()`.
- **Houdini async bridge**: Never call `asyncio.run()` directly in Houdini context. Use `run_async()` from `async_utils.py` which handles existing event loops.

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `DEEP_EARTH_ROOT` | Root path for Houdini package resolution |
| `DEEP_EARTH_GEE_SERVICE_ACCOUNT` | Google Earth Engine service account email |
| `DEEP_EARTH_GEE_KEY_PATH` | Path to GEE service account JSON key |
| `DEEP_EARTH_OPENTOPO_KEY` | OpenTopography API key |
| `HOUDINI_USER_PREF_DIR` | Houdini user preferences (used for cache default) |

## Current Development Plan

Active work is tracked in `conductor/tracks/phase7-production/plan.md` (Phases 7–9), consolidated from `production_spec.md`, `planet_embeddings_v3.md`, `docs/new_additons.md`, and the `product.md` roadmap.

- **Phase 7 — Repair & Stabilize**: Fix broken dev environment (`tenacity` missing), 7 failing tests, broken `verify_manual.py` imports, stale docs.
- **Phase 8 — Robustness**: Refactor `EarthEngineAdapter` to not crash callers, implement partial success in `Harmonizer`, add mock test fixtures for offline testing.
- **Phase 9 — Ship**: Verify HDA in Houdini 21.0, headless preview, wheel packaging, final docs.

### Current Test Status (as of plan creation)
- 46 passed, 7 failed, 8 collection errors
- Collection errors: `tenacity` not installed in `venv/`
- Failures: version assertion outdated, CLI test patching issues

## Commit Convention

```
<type>(<scope>): <description>
```
Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`. Conductor system uses `conductor(plan):` and `conductor(checkpoint):` prefixes.
