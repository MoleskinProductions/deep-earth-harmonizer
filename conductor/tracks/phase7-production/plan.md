# Phase 7–9: Production Readiness Plan

Consolidated from `production_spec.md`, `planet_embeddings_v3.md`,
`docs/new_additons.md`, `product.md` roadmap (Phases 4–6), and
current test suite results.

Items already completed by prior tracks are excluded.

### Baseline (2026-02-04)
- **Tests:** 85 passed, 0 failed, 0 errors
- **Coverage:** 72% overall (1002 stmts, 278 missed)
- **Low-coverage modules:** `earth_engine.py` (47%), `setup_wizard.py` (0%), `async_utils.py` (0%), `base.py` (76%)

---

## Phase 7: Repair & Stabilize
> Goal: Green test suite, working dev environment, no broken imports.

### 7.1 Fix Dev Environment
- [x] Install missing `tenacity` and `matplotlib` in `venv/`
- [x] Re-install package in dev mode (`pip install -e .`)
- [x] Verify all `pyproject.toml` dependencies import cleanly

### 7.2 Fix Broken Tests
- [x] Update `tests/test_package.py` version assertion from `"0.1.0"` to `"0.2.0"`
- [x] Fix `tests/test_cli.py` — root cause was package not installed in venv (resolved by `pip install -e .`)

### 7.3 Fix Broken Scripts
- [x] Update `verify_manual.py` to import `RegionContext` from `deep_earth.region` instead of deleted `deep_earth.bbox`

### 7.4 Clean Stale Documentation
- [x] Update `planet_embeddings_v3.md` with resolution status table; §1 items mostly resolved
- [x] Update `docs/new_additons.md` — items 1–4 marked done, item 5 linked to Phase 8.3
- [x] Update `product.md` Phase 4–6 roadmap to reflect completed conductor tracks

### 7.5 Establish Test Baseline
- [x] 85 passed, 0 failed, 0 errors
- [x] Coverage: 72% overall (see Baseline section above)

---

## Phase 8: Robustness & Fail-Graceful Hardening
> Goal: All provider failures handled gracefully; offline-testable suite.

### 8.1 EarthEngineAdapter Error Handling
- [x] `_fetch_batch` raises `RuntimeError` on task failure — refactored to return `None` with logging
- [x] `_ensure_initialized` returns `bool` instead of raising — defers initialization to `fetch()` time, tracks failure in `_init_error`
- [x] `_fetch_batch` returns `None` when no GCS bucket is configured — logs warning instead of raising `ValueError`

### 8.2 Harmonizer Partial Success
- [x] Added `FetchResult` dataclass and `process_fetch_result()` method to distinguish "no data" / "error" / "success"
- [x] `compute_quality_layer` correctly scores partial results when individual providers fail
- [x] Updated `houdini_hda_spec.md` and `hda_ir/deep_earth_harmonizer.json` to use `process_fetch_result` pattern

### 8.3 Mock Test Infrastructure
- [x] Added `tests/conftest.py` with `synthetic_dem` and `synthetic_embeddings` GeoTIFF fixtures
- [x] Added `mock_overpass_response` fixture with realistic Overpass JSON (roads, buildings, water, landuse)
- [x] All 106 provider tests run offline without network access or credentials
- [x] Added `mock_hou` fixture for Houdini geometry tests
- [x] Added `tests/test_ee_error_paths.py` (6 tests) and `tests/test_harmonize_integration.py` (5 tests)

### 8.4 CLI Error Paths
- [x] `deep-earth fetch` with invalid credentials prints JSON error and exits cleanly (no stack trace)
- [x] `deep-earth fetch` with unreachable APIs degrades gracefully — JSON output includes `errors` dict with per-provider messages
- [x] Added 3 new CLI tests: partial failure, invalid bbox, fatal error

### Phase 8 Baseline
- **Tests:** 106 passed, 0 failed, 0 errors
- **New tests added:** 14 (6 EE error paths + 5 harmonize integration + 3 CLI error paths)

---

## Phase 9: HDA Verification, Packaging & Release
> Goal: Ship a distributable package and verified HDA.

### 9.1 HDA Integration Verification
- [~] Verify `sop_mk.pv.deep_earth.1.0.hdalc` loads and cooks correctly in Houdini 21.0 — requires Houdini; code-level verification done
- [x] Verify `inject_heightfield` creates valid Houdini geometry (8 tests pass, uses `createPoints` API)
- [x] Verify `hda_ir/deep_earth_harmonizer.json` matches `houdini_hda_spec.md` (both use `process_fetch_result` pattern)
- [x] Credential status display logic (`creds.validate()` → `ee_status`/`ot_status`) verified via tests

### 9.2 Preview & Visualization
- [x] `preview.py` auto-detects headless environment and uses `Agg` backend; added `output_path` param for file saving
- [x] Added `--preview FILE` flag to `deep-earth fetch` CLI

### 9.3 Packaging & Distribution
- [x] Built `deep_earth-0.2.0-py3-none-any.whl` successfully
- [x] `deep-earth` entry point works from wheel install
- [x] Updated `planet_embeddings.json.template` path to `deep-earth-harmonizer`
- [x] Updated `docs/INSTALL.md` with wheel install, HDA package JSON (with credentials), and `preview` extra
- [x] Added `matplotlib` as optional `[preview]` dependency in `pyproject.toml`

### 9.4 Final Documentation
- [x] Updated `docs/QUICKSTART.md` — CLI output now shows structured `{"results": {...}, "errors": {...}}` format, added `--preview` param
- [x] Updated `docs/CREDENTIALS.md` — fixed stale `/path/to/planet_embeddings` references
- [x] `README.md` verified — no changes needed (links and commands are current)

### Phase 9 Baseline
- **Tests:** 107 passed, 0 failed, 0 errors
- **Wheel:** `dist/deep_earth-0.2.0-py3-none-any.whl` (builds and installs cleanly)
- **Note:** Full HDA load/cook test requires Houdini 21.0 environment

---

## Dependency Graph

```
Phase 7 (Repair)
  ├── 7.1 Fix Dev Environment
  │     └── 7.2 Fix Broken Tests (blocked by 7.1)
  │           └── 7.5 Establish Test Baseline (blocked by 7.2, 7.3)
  ├── 7.3 Fix Broken Scripts
  └── 7.4 Clean Stale Documentation (independent)

Phase 8 (Robustness) — blocked by 7.5
  ├── 8.1 EarthEngineAdapter Error Handling
  │     └── 8.2 Harmonizer Partial Success (blocked by 8.1)
  ├── 8.3 Mock Test Infrastructure (independent within Phase 8)
  └── 8.4 CLI Error Paths (blocked by 8.1)

Phase 9 (Ship) — blocked by Phase 8
  ├── 9.1 HDA Integration Verification
  ├── 9.2 Preview & Visualization
  ├── 9.3 Packaging & Distribution (blocked by 9.1)
  └── 9.4 Final Documentation (blocked by 9.3)
```

---

## Source Reconciliation

| Source Document | Status |
|---|---|
| `production_spec.md` §4 "Immediate Action Items" | All 3 items covered (7.3, 7.2/7.5, 8.2) |
| `production_spec.md` §3 "Work Plan" Phases 1–3 | Mapped to Phases 7–9 respectively |
| `planet_embeddings_v3.md` §1 "Immediate Attention" | Most resolved; residual items in 8.1, 9.1 |
| `docs/new_additons.md` items 1–5 | Items 1–4 implemented; item 5 (mock generators) → 8.3 |
| `product.md` Roadmap Phase 4 | CLI and preview exist; docstring/typing pass deferred (low priority) |
| `product.md` Roadmap Phase 5 | Point instancing → 9.1; EE batch → done; cache TTL → done; RegionContext → done |
| `product.md` Roadmap Phase 6 | PDG script exists; large region handling exists; HDA polish → 9.1; packaging → 9.3 |
| Current test failures (7 fail, 8 errors) | All addressed in 7.1 and 7.2 |
