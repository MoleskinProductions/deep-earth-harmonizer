import numpy as np

def inject_heightfield(geo, coordinate_manager, harmonizer, height_grid, embed_grid):
    """
    Injects elevation and embedding data into a Houdini heightfield.
    Note: This uses the 'hou' module which is only available inside Houdini.
    We use a generic 'geo' object to allow for some level of testing/mocking.
    """
    import hou
    
    # 1. Create/Resize Heightfield
    # Standard heightfield in Houdini is a volume with a 'height' layer
    # For simplicity in this foundation track, we'll assume the node creates 
    # the primitive and we just set its values.
    
    height_volumes = [v for v in geo.primitives() if v.type() == hou.primitiveType.Volume and v.name() == "height"]
    if not height_volumes:
        # Create height volume if it doesn't exist
        # This part usually happens in the SOP node setup, but we include it for completeness
        height_volume = geo.createVolume(harmonizer.width, harmonizer.height)
        height_volume.setName("height")
    else:
        height_volume = height_volumes[0]

    # 2. Set Elevation Data
    # Heightfield volumes are 2D but stored as 3D volumes with depth 1
    # We flatten the numpy array and set all voxels
    height_volume.setAllVoxels(height_grid.flatten())
    
    # 3. Inject Embeddings as Point Attributes
    # Create point attribute array 'embedding' [64]
    # We first convert the heightfield to points (standard Houdini practice for per-pixel attrs)
    # However, we can also store them as extra volumes (layers)
    
    # Option B: Point Attribute (as recommended in plan)
    # We'll create a point per grid cell
    geo.clearPoints()
    points = geo.createPoints(harmonizer.width * harmonizer.height)
    
    # Inject Embeddings
    attr_name = "embedding"
    geo.addAttrib(hou.attribType.Point, attr_name, (0.0,) * 64)
    flattened_embeddings = embed_grid.transpose(1, 2, 0).reshape(-1, 64)
    geo.setPointFloatAttribValues(attr_name, flattened_embeddings.flatten().tolist())
    
    # Inject Additional Layers from Harmonizer (OSM, etc.)
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
    
    # 4. Set P (Position) for points to match UTM grid
    # This aligns the point cloud with the heightfield
    
    # Generate grid of column and row indices
    cols, rows = np.meshgrid(np.arange(harmonizer.width), np.arange(harmonizer.height))
    
    # Calculate UTM coordinates (X=Easting, Y=Northing)
    # rasterio.transform * (cols, rows) returns (x, y)
    # We use (cols + 0.5, rows + 0.5) to get pixel centers
    xs, ys = harmonizer.dst_transform * (cols + 0.5, rows + 0.5)
    
    # In Houdini:
    # X = UTM Easting
    # Y = Elevation (height_grid)
    # Z = UTM Northing
    # Note: height_grid is usually (H, W)
    positions = np.stack([xs, height_grid, ys], axis=-1).reshape(-1, 3)
    
    geo.setPointFloatAttribValues("P", positions.flatten().tolist())
