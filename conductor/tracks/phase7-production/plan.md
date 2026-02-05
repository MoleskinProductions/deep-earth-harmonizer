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
- [ ] `_fetch_batch` raises `RuntimeError` on task failure — refactor to return `None` or a structured failure result instead of crashing callers that don't use `return_exceptions=True`
- [ ] `_ensure_initialized` raises `RuntimeError`/`ValueError` eagerly — defer initialization to `fetch()` time and return a clear error object so DEM/OSM-only cooks still work
- [ ] `_fetch_batch` raises `ValueError` when no GCS bucket is configured — log warning and return `None` with degraded `data_quality` instead

### 8.2 Harmonizer Partial Success
- [ ] Implement structured result handling in `Harmonizer` so callers can distinguish "no data" from "error" from "success"
- [ ] Ensure `compute_quality_layer` correctly scores partial results when individual providers fail
- [ ] Verify HDA internal Python SOP (`houdini_hda_spec.md` / `hda_ir`) handles all three provider failure modes without crashing the cook

### 8.3 Mock Test Infrastructure
- [ ] Add test fixtures that generate synthetic GeoTIFFs (elevation, 64-band embeddings) for offline harmonization tests
- [ ] Add mock Overpass API responses for OSM tests
- [ ] Ensure all provider tests can run without network access or credentials
- [ ] Add `hou` module stubs for Houdini geometry tests

### 8.4 CLI Error Paths
- [ ] Verify `deep-earth fetch` with invalid credentials prints useful error and exits cleanly (no stack trace)
- [ ] Verify `deep-earth fetch` with unreachable APIs degrades gracefully (partial JSON output)

---

## Phase 9: HDA Verification, Packaging & Release
> Goal: Ship a distributable package and verified HDA.

### 9.1 HDA Integration Verification
- [ ] Verify `sop_mk.pv.deep_earth.1.0.hdalc` loads and cooks correctly in Houdini 21.0 with updated `deep_earth` package
- [ ] Verify `inject_heightfield` creates valid Houdini geometry (uses correct `createPoints` API)
- [ ] Verify `hda_ir/deep_earth_harmonizer.json` matches the actual HDA state
- [ ] Confirm credential status display (`ee_status`, `ot_status` user data) works in HDA UI

### 9.2 Preview & Visualization
- [ ] Verify `preview.py` works headless (`matplotlib.use('Agg')`) for CI/server environments
- [ ] Add `--preview` flag to CLI for quick data verification without Houdini

### 9.3 Packaging & Distribution
- [ ] Build wheel: `python -m build` and verify it installs cleanly in a fresh venv
- [ ] Verify `deep-earth` entry point works from a wheel install
- [ ] Update `planet_embeddings.json.template` with current package paths
- [ ] Document HDA install steps (Houdini package file, PYTHONPATH, env vars) in `docs/INSTALL.md`

### 9.4 Final Documentation
- [ ] Ensure `docs/QUICKSTART.md` reflects current CLI interface
- [ ] Ensure `docs/CREDENTIALS.md` reflects current credential resolution order
- [ ] Update `README.md` if any user-facing commands or requirements changed

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
