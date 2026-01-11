# Deep Earth Harmonizer v3 – Architecture Review & Recommendations

## 1. Errors & Edge Cases That Need Immediate Attention
- **SciPy missing from the install manifest (`pyproject.toml:10-19`).** `terrain_analysis.py` and the OSM rasterization pipeline (`python/deep_earth/providers/osm.py`) import `scipy.ndimage`, but the dependency is not declared, so any fresh install of the wheel/CLI/HDA outside this repo will fail at import time.
- **Point instancing in Houdini is incorrect (`python/deep_earth/houdini/geometry.py:46-53`).** `hou.Geometry.createPoints` does not accept a raw count, so clearing the geometry and calling `createPoints(harmonizer.width * harmonizer.height)` will raise inside Houdini before any embeddings or attributes can be injected. We need to either call `createPoints` with explicit positions or iterate `createPoint`, then reposition via `setPointFloatAttribValues`.
- **Earth Engine export path cannot scale to production bboxes (`python/deep_earth/providers/earth_engine.py:58-121`).** The current `getDownloadURL` approach only works for very small tiles and will raise `EEException: Payload too large`. Per the `product-guidelines.md` fail-graceful principle we should switch to `ee.batch.Export.image.toDrive`/Cloud Storage with polling + timeout/backoff, and surface partial results with `f@data_quality` instead of throwing.
- **Cache metadata diverges from the stability spec (`python/deep_earth/cache.py:4-76`).** `cache_metadata.json` never records TTLs or versioned schemas the way `conductor/tracks/phase2-stability/spec.md` requires, so old entries never age out after a spec change and we cannot run cache migrations. We should store ISO8601 timestamps + TTL per entry and build a version bump path.
- **Bounding box lifecycle is duplicated (`python/deep_earth/bbox.py` vs `python/deep_earth/coordinates.py`).** Providers accept both `BoundingBox` and `CoordinateManager`, yet cache keys rely on attribute names that diverge between the two types. This inconsistently stringifies floats and risks double-fetching/corrupt caching when future CLI work (per `phase4-polish/plan.md`) starts instantiating `BoundingBox`. Consolidating to one canonical type keeps cache keys stable.
- **Credential/TOP failures abort the whole cook.** `EarthEngineAdapter.__init__` raises immediately when the EE service account is missing (`python/deep_earth/providers/earth_engine.py:21-43`), which prevents even DEM/OSM-only cooks from running. Product guidelines explicitly call for non-blocking logic, so adapters should lazily initialize and report availability via `data_quality`/status attributes instead of crashing the node.

## 2. Plan of Attack – Finalizing Functionality, Houdini Integration & Packaging
1. **Stabilize core data services**
   - Align caching with the stability spec: capture schema version, TTL per entry, and implement a lightweight migration path so artists can nuke stale entries from the UI.
   - Merge `BoundingBox` and `CoordinateManager` responsibilities behind a single dataclass that exposes WGS84, UTM, area metrics, and tile subdivision helpers (as promised in `product.md`). This keeps provider APIs consistent for both the HDA and the upcoming CLI.
   - Add SciPy (and other transitive requirements like `ee`, `rasterio[s3]` if remote exports are planned) to `pyproject.toml` and verify wheels build under Houdini’s Python 3.11.
   - Harden adapters: defer EE initialization until fetch time, add fallbacks (Drive/Cloud Storage export + signed URLs) with progress hooks, and surface per-provider status via structured logging (per `tech-stack.md` logging requirements) and Houdini string parms (`s@status_*`).

2. **Complete the Developer-Experience track (`conductor/tracks/phase4-polish`)**
   - Build `python/deep_earth/cli.py` with an `argparse` front end that wraps the same adapters used by the HDA. Respect `docs/CREDENTIALS.md` resolution order, emit JSON summaries, and allow prefetch-only flows so pipeline TDs can warm caches outside Houdini.
   - Add `python/deep_earth/__main__.py` + entry point so `python -m deep_earth --bbox ... --fetch-all` works for headless testing.
   - Implement `python/deep_earth/preview.py` to visualize DEM/PCA/OSM overlays via Matplotlib, sharing the PCA/biome helpers in `python/deep_earth/houdini/visualization.py`. This becomes the go-to Houdini-debug companion when artists need to verify data outside the DCC.
   - Enforce typing: add explicit `typing` imports + Google-style docstrings across adapters, harmonizer, Houdini helpers, and run `mypy --strict` (per spec) in CI and before shipping an OTL.

3. **Polish Houdini integration**
   - Update the HDA Python Module and internal Python SOP to follow `houdini_hda_spec.md`: fix menu handling (`parm.evalAsString()`), wrap fetches in `hou.InterruptableOperation`, and tag geometry with provenance (`s@source_year`, `f@data_quality`). Expose cache controls and credential diagnostics on the UI panel for faster troubleshooting.
   - Repair `inject_heightfield` so it creates points correctly, avoids clearing existing non-heightfield primitives, and writes `Cd`/embedding attributes lazily to minimize cook time. Add guards for missing layers so artists still see DEM-only output with a degraded quality mask.
   - Add PDG-ready hooks: encapsulate bbox tiling + cache exports so a TOP network can fan out tiles, then merge/clip back to Houdini heightfields as described in `product.md`.
   - Package distribution: version the digital asset (`otls/`), include the Python package inside the HDA’s `Scripts` section or ship it via a scoped Houdini package file, and document install steps in `docs/` so studio TDs can reproduce the setup.

4. **Debugging & QA workflow**
   - Wire the existing `logging_config.setup_logging` into both the CLI and Houdini module to emit matching log lines (per `conductor/tracks/phase2-stability/spec.md`), and expose a toggle on the HDA to open the latest log file.
   - Expand tests to cover Houdini stubs (mock `hou`) and CLI parsing, ensuring the fail-graceful behaviors (missing EE creds, Overpass outages, cache expiry) are enforced before artists touch the tool.

## 3. Future Additions & Pipeline Use Cases
- **Standalone utility ideas**
  - Tile queue + PDG-style batching from the CLI so artists or render wranglers can prep huge regions overnight, then load them instantly in Houdini via cached outputs.
  - Extend `terrain_analysis.py` outputs (slope/aspect/roughness/TWI) into a lightweight analytic bundle exported as GeoTIFFs, giving layout TDs data they can feed into other DCCs or generative tools.
  - Introduce additional providers (Sentinel-2, national LiDAR, climate rasters) behind the same adapter interface so the CLI becomes a general-purpose geospatial fetcher for the studio.

- **Pipeline & Houdini ecosystem integrations**
  1. **PDG/TOP orchestration:** wrap the adapters in TOP nodes so large-area requests can stream tiles into USD or Karma renders, leveraging the cache + status attributes for checkpointing.
  2. **Lookdev & VFX toolchains:** surface embeddings + OSM layers as USD primvars or MaterialX masks, enabling downstream shading, scattering, or FX solvers to respond to semantic classes.
  3. **Training/ML workflows:** reuse the CLI’s export path to generate labeled datasets (DEM + landuse + embeddings) that can train studio-specific placement models, then feed those models back into Houdini via VEX/VOP nodes.
  4. **Cross-DCC deployment:** because the core logic lives in `python/deep_earth`, we can expose the same functionality inside Unreal/Unity editor tools or as a headless microservice that feeds layout pipelines—keeping caches and credential handling consistent with the Houdini HDA.

These steps stay aligned with the design tenets in `conductor/product-guidelines.md`, leverage the tech stack defined in `conductor/tech-stack.md`, and close the gaps called out in the current track plan so we can package a reliable Deep Earth Harmonizer v2 for Houdini and headless workflows alike.
