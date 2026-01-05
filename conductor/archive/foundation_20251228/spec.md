# Track Spec: Foundation - Async Fetching and Harmonization

## Overview
This track focuses on the core data acquisition and alignment pipeline for the Deep Earth Harmonizer. It establishes the Python infrastructure for async communication with OpenTopography and Google Earth Engine, and implements the logic to synthesize these streams into a Houdini Heightfield.

## Scope
- **Credential Management:** Secure storage and retrieval of API keys and service account credentials.
- **Coordinate Manager:** UTM zone detection and WGS84 to UTM reprojection.
- **Elevation Provider:** Async fetching and caching of SRTM data from OpenTopography.
- **Embedding Provider:** Async fetching and caching of satellite embeddings from Google Earth Engine.
- **Harmonization Engine:** Resampling and grid alignment logic.
- **Houdini Integration:** A basic Python SOP that constructs the Heightfield and injects elevation and embedding attributes.

## Success Criteria
- Validated credentials for OpenTopography and GEE.
- Successful fetch and mosaic of SRTM elevation for a given bounding box.
- Successful fetch of 64D embeddings for the same region.
- Both data sources aligned on a UTM-based master grid.
- Houdini Heightfield correctly displaying elevation and storing embedding attributes.
