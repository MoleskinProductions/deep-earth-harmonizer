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
    """Injects elevation and embedding data as a Houdini point cloud.

    Creates one point per grid cell with UTM positions, elevation as
    both the Y coordinate and a ``height`` attribute, 64-band embeddings,
    and any additional harmonizer layers (OSM distance fields, etc.).

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

    # 1. Clear existing geometry and start fresh
    geo.clear()

    # 2. Create points at UTM grid locations
    cols, rows = np.meshgrid(
        np.arange(harmonizer.width), np.arange(harmonizer.height)
    )
    xs, ys = harmonizer.dst_transform * (cols + 0.5, rows + 0.5)

    # X = UTM Easting, Y = Elevation, Z = UTM Northing
    positions = np.stack([xs, height_grid, ys], axis=-1).reshape(-1, 3)
    points = geo.createPoints(positions.tolist())

    # 3. Explicit height attribute (mirrors Y position)
    geo.addAttrib(hou.attribType.Point, "height", 0.0)
    geo.setPointFloatAttribValues(
        "height", height_grid.flatten().tolist()
    )

    # 4. Inject embeddings as point attribute
    attr_name = "embedding"
    geo.addAttrib(hou.attribType.Point, attr_name, (0.0,) * 64)
    flattened_embeddings = embed_grid.transpose(1, 2, 0).reshape(-1, 64)
    geo.setPointFloatAttribValues(
        attr_name, flattened_embeddings.flatten().tolist()
    )

    # 5. Inject additional layers from Harmonizer (OSM, etc.)
    for name, data in harmonizer.layers.items():
        flattened_data = data.flatten()
        if np.issubdtype(data.dtype, np.floating):
            geo.addAttrib(hou.attribType.Point, name, 0.0)
            geo.setPointFloatAttribValues(
                name, flattened_data.tolist()
            )
        elif np.issubdtype(data.dtype, np.integer):
            geo.addAttrib(hou.attribType.Point, name, 0)
            geo.setPointIntAttribValues(
                name, flattened_data.tolist()
            )
        elif np.issubdtype(data.dtype, np.str_) or data.dtype == object:
            geo.addAttrib(hou.attribType.Point, name, "")
            geo.setPointStringAttribValues(
                name, flattened_data.tolist()
            )

    # 6. Visualization modes (Cd attribute)
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
                natural = harmonizer.layers.get("natural")
                if natural is not None:
                    colors = apply_biome_colors(natural).reshape(-1, 3)

        if colors is not None:
            geo.setPointFloatAttribValues(
                "Cd", colors.flatten().tolist()
            )

    # 7. Metadata & provenance (detail attributes)
    timestamp = datetime.now(timezone.utc).isoformat()
    geo.addAttrib(hou.attribType.Global, "fetch_timestamp", timestamp)

    if provenance:
        for key, value in provenance.items():
            attr_name = f"source_{key}" if key == "year" else key
            if isinstance(value, int):
                geo.addAttrib(
                    hou.attribType.Global, attr_name, value
                )
            else:
                geo.addAttrib(
                    hou.attribType.Global, attr_name, str(value)
                )
