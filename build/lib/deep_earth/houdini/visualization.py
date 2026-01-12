import numpy as np
from sklearn.decomposition import PCA
from typing import Dict, List, Optional, cast

def compute_pca_colors(embeddings: np.ndarray) -> np.ndarray:
    """
    Reduces high-dimensional embeddings to 3D using PCA and maps to [0, 1] for RGB.
    
    Args:
        embeddings: NumPy array of shape (N, D) or (D, H, W).
        
    Returns:
        NumPy array of shape (N, 3) representing RGB colors in range [0, 1].
    """
    if len(embeddings.shape) == 3:
        # (D, H, W) -> (H*W, D)
        d, h, w = embeddings.shape
        data = embeddings.transpose(1, 2, 0).reshape(-1, d)
    else:
        data = embeddings
        
    # Apply PCA to reduce to 3 components
    pca = PCA(n_components=3)
    pca_result = pca.fit_transform(data)
    
    # Normalize to [0, 1]
    # We use min-max scaling per component
    min_vals = pca_result.min(axis=0)
    max_vals = pca_result.max(axis=0)
    
    # Avoid division by zero
    range_vals = max_vals - min_vals
    range_vals[range_vals == 0] = 1.0
    
    normalized = (pca_result - min_vals) / range_vals
    return cast(np.ndarray, normalized)

def get_biome_color_map() -> Dict[str, List[float]]:
    """
    Returns a default mapping from landuse/natural tags to RGB colors.

    Returns:
        Dictionary mapping strings to 3-element lists of floats.
    """
    return {
        "forest": [0.1, 0.5, 0.1],
        "wood": [0.1, 0.4, 0.1],
        "grass": [0.4, 0.7, 0.2],
        "grassland": [0.4, 0.7, 0.2],
        "farmland": [0.6, 0.6, 0.2],
        "meadow": [0.5, 0.8, 0.3],
        "residential": [0.5, 0.5, 0.5],
        "commercial": [0.3, 0.3, 0.6],
        "industrial": [0.4, 0.3, 0.5],
        "water": [0.1, 0.3, 0.8],
        "scrub": [0.3, 0.4, 0.2],
        "heath": [0.4, 0.4, 0.2],
        "rock": [0.6, 0.6, 0.6],
        "bare_rock": [0.7, 0.7, 0.7],
        "sand": [0.9, 0.8, 0.5]
    }

def apply_biome_colors(landuse_data: np.ndarray, color_map: Optional[Dict[str, List[float]]] = None) -> np.ndarray:
    """
    Maps categorical landuse data (strings) to RGB colors.
    
    Args:
        landuse_data: NumPy array of shape (N,) or (H, W) containing strings.
        color_map: Optional custom color map.
        
    Returns:
        NumPy array of shape (..., 3) representing RGB colors.
    """
    if color_map is None:
        color_map = get_biome_color_map()
        
    shape = landuse_data.shape
    flattened = landuse_data.flatten()
    
    # Default color: Grey
    colors = np.full((len(flattened), 3), [0.5, 0.5, 0.5], dtype=np.float32)
    
    for label, color in color_map.items():
        mask = flattened == label
        colors[mask] = color
        
    return colors.reshape(shape + (3,))
