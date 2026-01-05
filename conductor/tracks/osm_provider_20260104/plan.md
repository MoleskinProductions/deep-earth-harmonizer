# Track Plan: OpenStreetMap (OSM) Provider Implementation

## Phase 1: Foundation & API Acquisition [checkpoint: 29f2334]
- [x] Task: Create `providers/osm.py` with `OverpassAdapter` shell and basic configuration. df1ef47
- [x] Task: Write tests for Overpass QL query generation and URL management. aa3d7b8
- [x] Task: Implement `OverpassAdapter._build_query` and API endpoint rotation logic. 91d0702
- [x] Task: Write tests for async data fetching and raw response caching. 9fbc436
- [x] Task: Implement `OverpassAdapter.fetch` (acquisition of raw JSON). 9fbc436
- [x] Task: Conductor - User Manual Verification 'Foundation & API Acquisition' (Protocol in workflow.md)

## Phase 2: Vector Parsing & Processing [checkpoint: cdda579]
- [x] Task: Write tests for JSON-to-Shapely geometry conversion. a9ca7ed
- [x] Task: Implement parsing logic to separate Roads, Water, Buildings, and Land Use. a9ca7ed
- [x] Task: Implement attribute extraction (e.g., `height` from building tags). a9ca7ed
- [x] Task: Conductor - User Manual Verification 'Vector Parsing & Processing' (Protocol in workflow.md)

## Phase 3: Rasterization Engine [checkpoint: 2cc669e]
- [x] Task: Write tests for distance field generation and binary masking. 21afd4c
- [x] Task: Implement `OverpassAdapter.transform_to_grid` using `rasterio.features.rasterize`. 21afd4c
- [x] Task: Implement distance field calculation for linear features (Roads, Waterways). 21afd4c
- [x] Task: Implement categorical mask generation for Land Use and Natural features. 21afd4c
- [x] Task: Conductor - User Manual Verification 'Rasterization Engine' (Protocol in workflow.md)

## Phase 4: Integration & Harmonization [checkpoint: 3b4bb2e]
- [x] Task: Write tests for integration within the main `Harmonizer` class. f6c172e
- [x] Task: Update `harmonize.py` to include OSM data in the master grid construction. f6c172e
- [x] Task: Verify end-to-end flow from bounding box to multi-layer attribute grid. f6c172e
- [x] Task: Conductor - User Manual Verification 'Integration & Harmonization' (Protocol in workflow.md)
