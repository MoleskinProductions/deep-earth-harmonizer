# Deep Earth Harmonizer - Final Houdini 21.0 Integration Spec (`final_houdini_ir.md`)

## Overview
This document outlines the final integration phase for Deep Earth Harmonizer with Houdini 21.0 using the Model Context Protocol (MCP). It defines the architecture for the "Houdini Bridge," specifies the new HDA features (Earth Engine Datasets, Harmonizer Agent), and details the roadmap for "tool calling" within Houdini.

## 1. Architecture: The MCP Houdini Bridge
The integration relies on an MCP server running locally that exposes the Deep Earth Python API as tools. Houdini acts as the MCP Client.

### Data Flow
1.  **Houdini (HDA)**: User adjusts parameters (BBox, Resolution, Dataset ID).
2.  **HDA Python Module**: Collects parameters and invokes the MCP Client.
3.  **MCP Server (`deep-earth-mcp`)**: Receives tool calls (e.g., `deep_earth_fetch`).
4.  **Deep Earth Core**: Executes the fetch/processing (async).
5.  **Response**: Returns structured JSON (paths to GeoTIFFs, metadata) to Houdini.
6.  **Houdini (COP/SOP)**: Ingests the resulting files via `@pdg_output` or file reads.

## 2. New Features

### 2.1. Earth Engine Dataset Repository
We will expose a curated list of Earth Engine datasets to the user, allowing them to override the default "Satellite Embeddings" with specific scientific data.

**Implementation Details:**
-   **Class**: `EarthEngineAdapter` extension.
-   **Method**: `get_available_datasets()` returning a list of dicts.
-   **UI**: HDA Dropdown menu for "Dataset Preset" + String Field for "Custom Asset ID".

**Initial Dataset List (Top 10):**
1.  **Sentinel-2**: `COPERNICUS/S2_SR_HARMONIZED` (10m Optical)
2.  **Landsat 9**: `LANDSAT/LC09/C02/T1_L2` (30m Optical)
3.  **Dynamic World**: `GOOGLE/DYNAMICWORLD/V1` (10m LULC Probabilities)
4.  **ESA WorldCover**: `ESA/WorldCover/v100` (10m Land Cover)
5.  **NASADEM**: `NASA/NASADEM_HGT/001` (30m Global Elevation)
6.  **ALOS World 3D**: `JAXA/ALOS/AW3D30/V2_2` (30m DSM)
7.  **ERA5 Land**: `ECMWF/ERA5_LAND/HOURLY` (11km Climate/Weather)
8.  **MODIS Land Cover**: `MODIS/006/MCD12Q1` (500m Annual LULC)
9.  **Global Forest Change**: `UMD/hansen/global_forest_change_2023_v1_11` (30m Forest cover)
10. **USGS SRTM**: `USGS/SRTMGL1_003` (30m Elevation - Base Truth)

### 2.2. Harmonizer Agent (Local Data Ingestion)
A flexible ingestion system for arbitrary terrestrial data stored locally.

**User Story:**
"The user points Deep Earth at a folder containing a dataset (e.g., Global LandCover). The Harmonizer scan the folder, identifies relevant files, and harmonizes them (projection, bounds) into the project."

**Implementation Details:**
-   **New Adapter**: `LocalFileAdapter`.
-   **Input**: Directory path or specific file path.
-   **Discovery**: Recursively scan for `.tif`, `.tiff`, `.jp2`.
-   **Harmonization**:
    -   Use `rasterio` to read metadata (CRS, Transform).
    -   Reproject to Project Region (UTM) using `Harmonizer.resample`.
    -   Merge logic: If multiple valid files cover the region, mosaic them.
-   **HDA UI**: New "Local Source" tab. Parameter "Input Directory".

**Test Case**: Global LandCover dataset integration.

## 3. Multiphase Implementation Plan

### Phase 1: Core Python Updates
-   [ ] Implement `get_available_datasets` in `EarthEngineAdapter`.
-   [ ] Modify `EarthEngineAdapter.fetch` to accept an `asset_id`.
-   [ ] Create `LocalFileAdapter` in `providers/local.py`.
-   [ ] Update `Harmonizer` to accept generic layers from `LocalFileAdapter`.

### Phase 2: CLI & Spec Updates
-   [ ] Update `cli.py` to support `--dataset-id` and `--local-dir`.
-   [ ] Verify "Global LandCover" ingestion via CLI.

### Phase 3: HDA & MCP Update
-   [ ] Update `deep_earth_harmonizer.json` (HDA IR) to include new parameters.
-   [ ] Update MCP Server to expose these new capabilities.
-   [ ] Verify full round-trip in Houdini 21.0.

## 4. MCP Tool Definitions
The MCP Server will expose the following tools:

-   `list_datasets()`: Returns the list of 10 EE datasets.
-   `fetch_region(bbox, resolution, datasets=[...], local_paths=[...])`: The master fetch command.
