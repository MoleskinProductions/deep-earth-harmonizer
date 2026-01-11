import numpy as np
import matplotlib.pyplot as plt
import logging
from typing import Any, Optional

from deep_earth.houdini.visualization import compute_pca_colors, apply_biome_colors

logger = logging.getLogger(__name__)

def generate_preview(data: np.ndarray, mode: str = "elevation", title: Optional[str] = None) -> None:
    """
    Generates a standalone visualization of the data using matplotlib.
    
    Args:
        data: NumPy array of the data to visualize.
        mode: Visualization mode ('elevation', 'pca', 'biome', 'osm').
        title: Optional title for the plot.
    """
    plt.figure(figsize=(10, 8))
    
    if mode == "elevation":
        plt.imshow(data, cmap="terrain")
        plt.colorbar(label="Elevation (m)")
    elif mode == "pca":
        # embeddings should be (64, H, W)
        if len(data.shape) == 3:
            h, w = data.shape[1], data.shape[2]
            colors = compute_pca_colors(data)
            plt.imshow(colors.reshape(h, w, 3))
        else:
            raise ValueError(f"PCA mode expects (D, H, W) data, got {data.shape}")
    elif mode == "biome":
        # landuse should be (H, W) strings
        colors = apply_biome_colors(data)
        plt.imshow(colors)
    elif mode == "osm":
        # Assume data is a dictionary of layers or a combined mask
        if isinstance(data, dict):
            # Simple overlay: elevation + road/water masks
            elev = data.get("elevation")
            if elev is not None:
                plt.imshow(elev, cmap="gray", alpha=0.8)
            
            roads = data.get("road_distance")
            if roads is not None:
                # Show roads as thin lines where distance is low
                plt.contour(roads, levels=[10], colors="white", linewidths=1)
                
            water = data.get("water_distance")
            if water is not None:
                plt.contour(water, levels=[10], colors="blue", linewidths=1)
        else:
            plt.imshow(data)
    else:
        raise ValueError(f"Unknown visualization mode: {mode}")
        
    if title:
        plt.title(title)
    plt.axis("off")
    plt.show()

if __name__ == "__main__":
    # Example usage for testing
    dummy_dem = np.random.rand(100, 100) * 1000
    generate_preview(dummy_dem, mode="elevation", title="Elevation Test")
