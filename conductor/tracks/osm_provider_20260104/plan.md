# Track Plan: OpenStreetMap (OSM) Provider Implementation

## Phase 1: Foundation & API Acquisition [checkpoint: pending]
- [~] Task: Create `providers/osm.py` with `OverpassAdapter` shell and basic configuration.
- [ ] Task: Write tests for Overpass QL query generation and URL management.
- [ ] Task: Implement `OverpassAdapter._build_query` and API endpoint rotation logic.
- [ ] Task: Write tests for async data fetching and raw response caching.
- [ ] Task: Implement `OverpassAdapter.fetch` (acquisition of raw JSON).
- [ ] Task: Conductor - User Manual Verification 'Foundation & API Acquisition' (Protocol in workflow.md)

## Phase 2: Vector Parsing & Processing [checkpoint: pending]
- [ ] Task: Write tests for JSON-to-Shapely geometry conversion.
- [ ] Task: Implement parsing logic to separate Roads, Water, Buildings, and Land Use.
- [ ] Task: Implement attribute extraction (e.g., `height` from building tags).
- [ ] Task: Conductor - User Manual Verification 'Vector Parsing & Processing' (Protocol in workflow.md)

## Phase 3: Rasterization Engine [checkpoint: pending]
- [ ] Task: Write tests for distance field generation and binary masking.
- [ ] Task: Implement `OverpassAdapter.transform_to_grid` using `rasterio.features.rasterize`.
- [ ] Task: Implement distance field calculation for linear features (Roads, Waterways).
- [ ] Task: Implement categorical mask generation for Land Use and Natural features.
- [ ] Task: Conductor - User Manual Verification 'Rasterization Engine' (Protocol in workflow.md)

## Phase 4: Integration & Harmonization [checkpoint: pending]
- [ ] Task: Write tests for integration within the main `Harmonizer` class.
- [ ] Task: Update `harmonize.py` to include OSM data in the master grid construction.
- [ ] Task: Verify end-to-end flow from bounding box to multi-layer attribute grid.
- [ ] Task: Conductor - User Manual Verification 'Integration & Harmonization' (Protocol in workflow.md)
