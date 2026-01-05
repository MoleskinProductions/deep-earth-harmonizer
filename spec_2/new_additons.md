# New Additions & Next Steps

Based on the analysis of the current project state (spec v1 vs implementation), here are the recommended next steps:

## 1. Implement OpenStreetMap (OSM) Provider
**Status:** Specified in `conductor/product.md` but missing in `python/deep_earth/providers/`.
**Goal:** Create `osm.py` to fetch vector data via Overpass API and rasterize it.
- Implement `OverpassAdapter` class inheriting from `DataProviderAdapter`.
- Add logic to query roads, waterways, and buildings.
- Implement rasterization strategies (distance fields, binary masks).

## 2. CLI / Standalone Runner
**Status:** Currently logic is designed to be called from Houdini.
**Goal:** Create a `__main__.py` or `cli.py` to allow running the pipeline from the terminal.
- Allow passing bounding box and resolution arguments.
- useful for debugging and testing without launching Houdini.
- Example: `python -m deep_earth.cli --lat 45.0 45.1 --lon -93.0 -92.9 --fetch-all`

## 3. Visualization Tools
**Status:** Visualization is currently relied upon Houdini's viewport.
**Goal:** Add a simple visualization module (e.g., using `matplotlib`).
- Preview downloaded GeoTIFFs (SRTM, Embeddings).
- Overlay OSM data for verification.
- Helpful for verifying alignment before importing into Houdini.

## 4. Enhanced Error Handling & Logging
**Status:** Basic exception handling exists.
**Goal:** robust logging system.
- Log fetches to a file.
- Better user feedback for API failures (e.g., specific GEE quota errors).

## 5. Mock Data Generators
**Status:** Tests rely on some mocks, but a robust mock data generator would be useful for offline development.
- Generate synthetic GeoTIFFs for testing harmonization without network calls.
