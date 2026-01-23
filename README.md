# Deep Earth Harmonizer

**Multi-modal geospatial data synthesizer for Houdini**

Deep Earth Harmonizer fetches and fuses data from multiple geospatial sources into unified terrain for procedural world-building in Houdini.

## What It Does

- **SRTM Elevation** - 30m resolution digital elevation from OpenTopography
- **Satellite Embeddings** - 64-band ML embeddings from Google Earth Engine
- **OSM Vector Data** - Roads, buildings, waterways from OpenStreetMap

All three sources are harmonized to a common grid and injected as Houdini heightfield layers with per-point attributes.

## Key Features

- **Async Fetching** - All data sources fetched concurrently
- **Smart Caching** - Results cached locally to avoid redundant API calls
- **Fail-Graceful** - Missing data sources don't block the pipeline
- **Houdini Integration** - Native HDA with button-click workflow

## Quick Install

```bash
pip install -e .
deep-earth setup
```

See [docs/INSTALL.md](docs/INSTALL.md) for detailed installation instructions.

## Quick Start

```bash
# Fetch data for downtown Minneapolis
deep-earth fetch --bbox 44.97,-93.27,44.98,-93.26 --resolution 10
```

See [docs/QUICKSTART.md](docs/QUICKSTART.md) for a complete walkthrough.

## Documentation

- [INSTALL.md](docs/INSTALL.md) - Full installation guide
- [QUICKSTART.md](docs/QUICKSTART.md) - First fetch walkthrough
- [CREDENTIALS.md](docs/CREDENTIALS.md) - API credential setup

## Requirements

- Python 3.9+
- Houdini 21.0+ (for HDA)
- Google Earth Engine service account
- OpenTopography API key

## License

MIT
