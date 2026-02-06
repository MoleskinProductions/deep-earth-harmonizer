# Deep Polish Pass - Cleanup & Housekeeping (`deep_polish_pass.md`)

## Overview
This document tracks "last minute" necessary edits, code cleanup, and housekeeping items to ensure the `deep-earth-harmonizer` repository is production-ready.

## 1. Code Cleanup & Refactoring

### 1.1. CLI (`python/deep_earth/cli.py`)
- [ ] **Refactor `run_fetch_all`**: Currently, it instantiates adapters directly. It should accept dependency injection for easier testing.
- [ ] **Error Handling**: `sys.exit(1)` in `main_logic` is abrupt. Ensure cleaner exception propagation for library use.

### 1.2. Earth Engine Adapter (`python/deep_earth/providers/earth_engine.py`)
- [ ] **DRY Logic**: The `_ensure_initialized` check is repeated. Consider a `@require_gee` decorator.
- [ ] **Type Hinting**: Improve typings for `ee` objects (use `Any` or `ee.Image` where possible, though `ee` library types are tricky).

### 1.3. Harmonizer (`python/deep_earth/harmonize.py`)
- [ ] **Configurable Quality**: `compute_quality_layer` has hardcoded weights (0.25, 0.5, etc.). Move these to `Config` or allow overrides.

### 1.4. General
- [ ] **Imports**: Sort imports using `isort` logic (standard library -> third party -> local).
- [ ] **Docstrings**: Ensure all public methods in `RegionContext` and `Harmonizer` have Google-style docstrings.

## 2. Documentation Updates

### 2.1. README.md
- [ ] **Feature List**: Add "Earth Engine Dataset Repository" and "Local Data Ingestion".
- [ ] **Houdini Compat**: Update version badge to "Houdini 21.0 Ready".

### 2.2. Requirements
- [ ] **Verify Dependencies**: Ensure `rasterio`, `numpy`, and `earthengine-api` versions in `pyproject.toml` are pinned to stable versions compatible with Python 3.9+.

## 3. Testing
- [ ] **New Tests**: Add unit tests for `LocalFileAdapter`.
- [ ] **Integration**: manual test script `verify_manual.py` needs to include the new local ingestion step.

## 4. HDA Housekeeping
- [ ] **Version Bump**: Update HDA version to `1.1` in `hda_ir` and filename.
- [ ] **Icon**: Ensure the HDA icon is correctly set (currently `SOP_heightfield`).

## 5. File Sweep
- [ ] Check `scripts/` directory for any stray temporary scripts.
- [ ] Ensure `.gitignore` covers all cache directories (`deep_earth_cache`, `__pycache__`).
