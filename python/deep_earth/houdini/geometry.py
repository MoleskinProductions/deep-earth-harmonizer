from typing import Any, Dict, Optional

import numpy as np

from deep_earth.harmonize import Harmonizer
from deep_earth.houdini.visualization import apply_biome_colors, compute_pca_colors
from deep_earth.region import RegionContext

def inject_heightfield(
    geo: Any, 
    coordinate_manager: RegionContext, 
    harmonizer: Harmonizer, 
    height_grid: np.ndarray, 
    embed_grid: np.ndarray, 
    viz_mode: Optional[str] = None,
    provenance: Optional[Dict[str, Any]] = None
) -> None:
    """
    Injects elevation and embedding data into a Houdini heightfield.
    
    Note: This uses the 'hou' module which is only available inside Houdini.
    We use a generic 'geo' object to allow for some level of testing/mocking.
    
    Args:
        geo: The Houdini geometry object (hou.Geometry).
        coordinate_manager: The RegionContext instance for the region.
        harmonizer: The Harmonizer instance containing resampled layers.
        height_grid: (H, W) elevation grid.
        embed_grid: (64, H, W) embedding grid.
        viz_mode: Optional visualization mode ('pca', 'biome').
        provenance: Optional metadata dictionary (e.g., source_year).
    """
    import hou
    from datetime import datetime, timezone
    
    # 1. Create/Resize Heightfield
    # Standard heightfield in Houdini is a volume with a 'height' layer
    # For simplicity in this foundation track, we'll assume the node creates 
    # the primitive and we just set its values.
    
    _prims = geo.prims() if hasattr(geo, 'prims') else geo.primitives()
    height_volumes = [v for v in _prims if v.type() == hou.primitiveType.Volume and v.name() == "height"]
    if not height_volumes:
        # Create height volume if it doesn't exist
        # This part usually happens in the SOP node setup, but we include it for completeness
        height_volume = geo.createVolume(harmonizer.width, harmonizer.height, 1)
        height_volume.setName("height")
    else:
        height_volume = height_volumes[0]

    # 2. Set Elevation Data
    # Heightfield volumes are 2D but stored as 3D volumes with depth 1
    # We flatten the numpy array and set all voxels
    height_volume.setAllVoxels(height_grid.flatten())
    
    # Option B: Point Attribute (as recommended in plan)
    # 3. Create Points at UTM grid locations
    # We create a point per grid cell to store embeddings and other attributes
    if hasattr(geo, 'clearPoints'):
        geo.clearPoints()
    else:
        geo.clear()
    
    # Generate grid of column and row indices
    cols, rows = np.meshgrid(np.arange(harmonizer.width), np.arange(harmonizer.height))
    
    # Calculate UTM coordinates (X=Easting, Y=Northing)
    # We use (cols + 0.5, rows + 0.5) to get pixel centers
    xs, ys = harmonizer.dst_transform * (cols + 0.5, rows + 0.5)
    
    # In Houdini:
    # X = UTM Easting
    # Y = Elevation (height_grid)
    # Z = UTM Northing
    positions = np.stack([xs, height_grid, ys], axis=-1).reshape(-1, 3)
    
    # Create points with explicit positions
    # Note: positions.flatten().tolist() might be slow for very large grids, 
    # but it's the standard way to pass from NumPy to hou
    points = geo.createPoints(positions.tolist())
    
    # 4. Inject Embeddings as Point Attributes
    attr_name = "embedding"
    geo.addAttrib(hou.attribType.Point, attr_name, (0.0,) * 64)
    flattened_embeddings = embed_grid.transpose(1, 2, 0).reshape(-1, 64)
    geo.setPointFloatAttribValues(attr_name, flattened_embeddings.flatten().tolist())
    
    # 5. Inject Additional Layers from Harmonizer (OSM, etc.)
    for name, data in harmonizer.layers.items():
        flattened_data = data.flatten()
        if np.issubdtype(data.dtype, np.floating):
            geo.addAttrib(hou.attribType.Point, name, 0.0)
            geo.setPointFloatAttribValues(name, flattened_data.tolist())
        elif np.issubdtype(data.dtype, np.integer):
            geo.addAttrib(hou.attribType.Point, name, 0)
            geo.setPointIntAttribValues(name, flattened_data.tolist())
        elif np.issubdtype(data.dtype, np.str_) or data.dtype == object:
            geo.addAttrib(hou.attribType.Point, name, "")
            geo.setPointStringAttribValues(name, flattened_data.tolist())
    
    # 6. Visualization Modes (Cd attribute)
    if viz_mode:
        geo.addAttrib(hou.attribType.Point, "Cd", (1.0, 1.0, 1.0))
        colors = None
        
        if viz_mode == "pca":
            colors = compute_pca_colors(embed_grid)
        elif viz_mode == "biome":
            landuse = harmonizer.layers.get("landuse")
            if landuse is not None:
                colors = apply_biome_colors(landuse).reshape(-1, 3)
            else:
                # Try 'natural' layer if landuse is missing
                natural = harmonizer.layers.get("natural")
                if natural is not None:
                    colors = apply_biome_colors(natural).reshape(-1, 3)
        
        if colors is not None:
            geo.setPointFloatAttribValues("Cd", colors.flatten().tolist())

    # 7. Metadata & Provenance (Detail attributes)
    timestamp = datetime.now(timezone.utc).isoformat()
    geo.addAttrib(hou.attribType.Global, "fetch_timestamp", timestamp)
    
    if provenance:
        for key, value in provenance.items():
            attr_name = f"source_{key}" if key == "year" else key
            if isinstance(value, int):
                geo.addAttrib(hou.attribType.Global, attr_name, value)
            else:
                geo.addAttrib(hou.attribType.Global, attr_name, str(value))
