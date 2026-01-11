# Advanced Houdini & PDG - Specification

## Provenance Schema

| Attribute | Type | Description |
|-----------|------|-------------|
| `s@source_year` | string | Year of the embedding/satellite data |
| `s@fetch_timestamp` | string | ISO8601 time of data acquisition |
| `s@provider_errors` | string | JSON list of any non-fatal provider errors |

## PDG Tile Workflow

1. **Partition:** TOP node splits main bbox into N tiles.
2. **Fetch & Cache:** N work items fetch their specific bboxes independently.
3. **Harmonize:** N work items create `.bgeo.sc` files.
4. **Merge:** Houdini SOP merges geometry and stitches heightfield seams.

## Versioning

HDA name: `mk::deep_earth::1.0`
Python version: `0.2.0` (Hardening + Advanced)
