# Advanced Houdini & PDG - Plan

## Goal
Deepen Houdini integration, support large-scale orchestration via PDG, and prepare for distribution.

## Tasks

### 6.1 HDA UI & UX Polish
- [ ] Fix menu handling in HDA Python module (use `parm.evalAsString()`)
- [ ] Implement `hou.InterruptableOperation` for all fetching tasks
- [ ] Add credential diagnostic panel to the HDA UI

### 6.2 Attributes & Provenance
- [ ] Add `s@source_year` attribute to all generated geometry
- [ ] Add `s@provider_status_*` attributes for debugging source availability
- [ ] Refactor `inject_heightfield` to write attributes lazily

### 6.3 PDG Orchestration
- [ ] Add `get_tiles()` helper to Region Context for TOP network fan-out
- [ ] Implement a TOPs-ready script for per-tile fetching and harmonization
- [ ] Create example TOP network for processing large regions (>100km2)

### 6.4 Distribution Packaging
- [ ] Version the HDA (`otls/`) using standard Houdini versioning
- [ ] Document final install steps for studio environments
- [ ] Create a consolidated "Deep Earth Setup" wizard script

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
