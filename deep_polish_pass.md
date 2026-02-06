# Deep Polish Pass - Cleanup & Housekeeping (`deep_polish_pass.md`)

## Overview
This document tracks "last minute" necessary edits, code cleanup, and housekeeping items to ensure the `deep-earth-harmonizer` repository is production-ready.

## 1. Code Cleanup & Refactoring

### 1.1. CLI (`python/deep_earth/cli.py`)
- [x] **Refactor `run_fetch_all`**: Accepts `adapters` dict for dependency injection.
- [x] **Error Handling**: `main_logic` raises `CLIError`; `main()` catches and translates to `sys.exit`. Clean for library use.

### 1.2. Earth Engine Adapter (`python/deep_earth/providers/earth_engine.py`)
- [x] **DRY Logic**: `@require_ee` decorator handles initialization checks.
- [ ] **Type Hinting**: Improve typings for `ee` objects (use `Any` or `ee.Image` where possible, though `ee` library types are tricky).

### 1.3. Harmonizer (`python/deep_earth/harmonize.py`)
- [x] **Configurable Quality**: `compute_quality_layer` uses weights from `Config`.

### 1.4. General
- [x] **Imports**: Sorted imports using isort convention (stdlib -> third-party -> local).
- [x] **Docstrings**: Public methods in `RegionContext` and `Harmonizer` have Google-style docstrings.

## 2. Documentation Updates

### 2.1. README.md
- [x] **Feature List**: Added "Earth Engine Dataset Repository", "Local Data Ingestion", and "MCP Tools".
- [x] **Houdini Compat**: Updated to "Houdini 21.0+ (for HDA integration)".

### 2.2. Requirements
- [x] **Verify Dependencies**: Relaxed exact pins to `>=` ranges compatible with Python 3.9+.

## 3. Testing
- [x] **New Tests**: Added unit tests for `LocalFileAdapter` (`tests/test_local.py`, 8 tests).
- [x] **Integration**: `verify_manual.py` already includes local ingestion step. Fixed dead `test_preview()` reference.

## 4. HDA Housekeeping
- [ ] **Version Bump**: Update HDA version to `1.1` in `hda_ir` and filename.
- [ ] **Icon**: Ensure the HDA icon is correctly set (currently `SOP_heightfield`).

## 5. File Sweep
- [x] Check `scripts/` directory for any stray temporary scripts. (Clean)
- [x] Ensure `.gitignore` covers all cache directories (`deep_earth_cache`, `__pycache__`).
- [x] Remove stale `build/` artifacts from git tracking.
