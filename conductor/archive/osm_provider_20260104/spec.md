# Track Specification: Implement OpenStreetMap (OSM) Provider

## Overview
This track implements the `OSMAdapter` in `python/deep_earth/providers/osm.py` to fetch, cache, and rasterize vector infrastructure data from OpenStreetMap via the Overpass API. This completes the three-pronged data strategy (Elevation, Embeddings, and Vectors) defined in the product guide.

## Functional Requirements
- **Data Acquisition:**
  - Implement `OverpassAdapter` class inheriting from `DataProviderAdapter`.
  - Fetch features using Overpass QL based on a bounding box.
  - Prioritize five categories: Roads (`highway=*`), Waterways (`waterway=*`), Buildings (`building=*`), Land Use (`landuse=*`), and Natural features (`natural=*`).
- **Rasterization & Harmonization:**
  - **Linear Features (Roads, Waterways):** Convert to 32-bit float distance fields (meters from feature).
  - **Area Features (Buildings):** Convert to binary masks and extract `height` tags (float) where available.
  - **Categorical Features (Land Use, Natural):** Convert to integer ID masks.
- **Service Management:**
  - Use a public Overpass API instance by default.
  - Support configurable fallback URLs and prepare the structure for future local archive support.
- **Caching:**
  - Implement disk-based caching of the raw Overpass JSON response in `conductor/tracks/osm/`.

## Non-Functional Requirements
- **Async Support:** Network calls must be non-blocking using `aiohttp`.
- **Performance:** Rasterization should be optimized using `numpy` and `shapely` or `rasterio.features.rasterize`.
- **Robustness:** Gracefully handle empty responses (e.g., no roads in the desert) by providing zeroed or high-distance arrays rather than failing.

## Acceptance Criteria
- [ ] `osm.py` created with `OverpassAdapter` class.
- [ ] Successful fetch and JSON caching for a 2km x 2km test region.
- [ ] Successful rasterization of roads into a `road_distance` attribute.
- [ ] Successful rasterization of buildings into `building_mask` and `building_height`.
- [ ] Unit tests covering API fetching (mocked), JSON parsing, and rasterization logic.
- [ ] >80% code coverage for the new module.

## Out of Scope
- Direct import of `.osm` or `.pbf` files (reserved for future "Local Archive" track).
- Complex road network topology (e.g., junction analysis) beyond simple proximity.
