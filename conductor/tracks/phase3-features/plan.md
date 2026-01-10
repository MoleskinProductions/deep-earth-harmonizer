# Feature Completion - Plan

## Goal
Implement missing spec features for Houdini integration.

## Tasks

### 3.1 Houdini Geometry Injection
- [x] Implement point position calculation based on UTM grid transform (3cb61d8)
- [x] Add OSM attribute injection (`s@highway`, `f@road_distance`, etc.) (3efb819)
- [x] Add visualization modes (PCA embeddings, biome colors) (29cd937)

### 3.2 Derived Terrain Attributes
- [x] Add `compute_slope()` — gradient magnitude (4428a81)
- [x] Add `compute_aspect()` — gradient direction (0-360°) (4428a81)
- [x] Add `compute_curvature()` — second derivative (4428a81)
- [x] Add `compute_roughness()` — local variance (4428a81)
- [x] Add `compute_tpi()` — Topographic Position Index (4428a81)
- [x] Add `compute_twi()` — Topographic Wetness Index (4428a81)

### 3.3 Data Quality Tracking
- [ ] Add `data_quality` field to Harmonizer output
- [ ] Score based on available sources (all=1.0, DEM only=0.25)
- [ ] Inject as `f@data_quality` attribute in Houdini

## Files to Modify
| Action | File |
|--------|------|
| MODIFY | `python/deep_earth/houdini/geometry.py` |
| NEW | `python/deep_earth/houdini/visualization.py` |
| NEW | `python/deep_earth/terrain_analysis.py` |
| MODIFY | `python/deep_earth/harmonize.py` |
| NEW | `tests/test_terrain_analysis.py` |

## Verification
```bash
pytest tests/test_terrain_analysis.py -v
# Manual: Load in Houdini, verify attributes in Geometry Spreadsheet
```
