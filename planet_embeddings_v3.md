# Deep Earth Harmonizer v3 – Architecture Review & Recommendations

> **Status as of 2026-02-04:** Most §1 items have been resolved. Remaining
> work is tracked in `conductor/tracks/phase7-production/plan.md` (Phases 7–9).

## 1. Errors & Edge Cases — Resolution Status

| Issue | Status | Notes |
|-------|--------|-------|
| SciPy missing from `pyproject.toml` | **Resolved** | Added in Production Hardening track |
| Point instancing in `geometry.py` | **Open** | Needs Houdini-side verification (Phase 9.1) |
| EE export path cannot scale | **Partially resolved** | Batch export via GCS implemented; error handling still raises `RuntimeError` (Phase 8.1) |
| Cache metadata diverges from spec | **Resolved** | CacheManager v2 with ISO8601 timestamps and TTL |
| Bounding box lifecycle duplicated | **Resolved** | Consolidated to `RegionContext` in `region.py`; backward compat aliases in place |
| Credential/TOP failures abort cook | **Partially resolved** | EE init deferred to `fetch()` but still raises on failure (Phase 8.1) |

## 2. Plan of Attack — Resolution Status

1. **Stabilize core data services** — **Resolved.** Cache aligned, bbox consolidated, scipy added, adapters use lazy init.
2. **Developer Experience track** — **Resolved.** CLI (`cli.py`), `__main__.py`, `preview.py`, and docstrings implemented.
3. **Houdini integration polish** — **Partially resolved.** HDA spec, PDG tile script, and IR format exist. Point instancing and packaging need verification (Phase 9).
4. **Debugging & QA workflow** — **Partially resolved.** Logging infrastructure exists. Mock test expansion planned (Phase 8.3).

## 3. Future Additions & Pipeline Use Cases

These remain valid aspirational goals and are not part of the current production plan:

- Tile queue + PDG-style batching from the CLI
- Terrain analysis GeoTIFF exports for cross-DCC use
- Additional providers (Sentinel-2, LiDAR, climate rasters)
- USD primvar / MaterialX mask export
- Training/ML dataset generation workflows
- Cross-DCC deployment (Unreal/Unity)
