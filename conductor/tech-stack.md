# Technology Stack

This document outlines the core technologies and dependencies used in the Deep Earth Harmonizer project.

## Infrastructure & Tools
- **DCC Platform:** Houdini 21.0+
- **Language:** Python 3.11+ (Houdini 21.0 default)


## Geospatial Libraries
- **pyproj:** Handling coordinate reference system (CRS) transformations, specifically WGS84 to UTM.
- **shapely:** Performing geometric operations, bounding box validation, and tile subdivision.
- **rasterio:** reading and writing GeoTIFF data, mosaic creation, and high-performance resampling.
- **numpy:** The foundation for all grid-based data manipulation, from elevation arrays to 64D embedding vectors.
- **scipy:** Utilized for high-performance distance field computations (Euclidean Distance Transform) during OSM vector rasterization.
- **matplotlib:** Powering standalone 2D data previews and diagnostic visualizations.

## Data Provider Integrations
- **OpenTopography API:** Primary source for SRTM and global elevation datasets.
- **Google Earth Engine (GEE) API:** Accessing the 64-dimensional satellite embedding ImageCollections.
- **Overpass API (OSM):** Querying and fetching vector infrastructure data (roads, buildings, land use).

## Performance & Scaling
- **asyncio & aiohttp:** enabling non-blocking, parallel network requests for data fetching.
- **tenacity:** providing exponential backoff and retry logic for robust external API interactions.
- **logging:** centralized infrastructure for file and console-based system monitoring.
- **Houdini PDG (TOPs):** Orchestrating large-scale processing by distributing tile-based work items.
- **VEX:** Used within Houdini SOPs for per-point attribute calculations and semantic filtering to ensure viewport responsiveness.

## Machine Learning
- **scikit-learn:** Utilized for downstream semantic operations like K-Means clustering of satellite embeddings into biomes.

## Development & Distribution
- **Standalone Python Package:** Logic is encapsulated in a `deep_earth` package to allow for unit testing and modularity.
- **Houdini HDA Wrapper:** Digital Assets provide the artist-facing UI and bridge the Python logic into the Houdini scene graph.
