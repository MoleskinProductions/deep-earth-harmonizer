# Advanced Houdini & PDG - Plan

## Goal
Deepen Houdini integration, support large-scale orchestration via PDG, and prepare for distribution.

## Tasks

### 6.1 HDA UI & UX Polish
- [x] Fix menu handling in HDA Python module (use `parm.evalAsString()`) (c1399d0)
- [x] Implement `hou.InterruptableOperation` for all fetching tasks (c1399d0)
- [x] Add credential diagnostic panel to the HDA UI (c1399d0)

### 6.2 Attributes & Provenance
- [x] Add `s@source_year` attribute to all generated geometry (690c880)
- [x] Add `s@provider_status_*` attributes for debugging source availability (690c880)
- [x] Refactor `inject_heightfield` to write attributes lazily (690c880)

### 6.3 PDG Orchestration
- [x] Add `get_tiles()` helper to Region Context for TOP network fan-out (3c43d0d)
- [x] Implement a TOPs-ready script for per-tile fetching and harmonization (3c43d0d)
- [x] Create example TOP network for processing large regions (>100km2) (3c43d0d)

### 6.4 Distribution Packaging
- [x] Version the HDA (`otls/`) using standard Houdini versioning (b981a36)
- [x] Document final install steps for studio environments (b981a36)
- [x] Create a consolidated "Deep Earth Setup" wizard script (b981a36)

## Files to Modify
| Action | File |
|--------|------|
| MODIFY | `otls/deep_earth_harmonizer.hda` (Manual) |
| MODIFY | `houdini_hda_spec.md` |
| MODIFY | `python/deep_earth/houdini/geometry.py` |
| NEW | `scripts/deep_earth_pdg_tile.py` |

## Verification
- Load 100km2 region via PDG TOP network.
- Verify seamless stitching of heightfield tiles.
- Check provenance attributes in Geometry Spreadsheet.
