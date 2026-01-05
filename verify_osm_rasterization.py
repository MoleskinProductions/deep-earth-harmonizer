import numpy as np
from unittest.mock import MagicMock, patch
from shapely.geometry import LineString, Polygon
from deep_earth.providers.osm import OverpassAdapter

def verify():
    # Setup a mock grid
    grid = MagicMock()
    grid.width = 100
    grid.height = 100
    grid.dst_transform = [1.0, 0, 0, 0, -1.0, 100]
    grid.dst_crs = 'EPSG:3857'

    # Mock data with a road and a building
    data = [
        {
            'type': 'road', 
            'geometry': LineString([(0, 50), (100, 50)]), 
            'tags': {'highway': 'primary'}
        },
        {
            'type': 'building', 
            'geometry': Polygon([(40, 40), (40, 60), (60, 60), (60, 40), (40, 40)]),
            'tags': {'building': 'house', 'height': 10.0}
        }
    ]

    adapter = OverpassAdapter()

    # Patch pyproj to avoid actual coordinate transformations in this simple test
    with patch('pyproj.Transformer.from_crs') as MockTrans:
        MockTrans.return_value.transform.side_effect = lambda x, y: (x, y)
        
        layers = adapter.transform_to_grid(data, grid)
        
        print(f"Layers created: {list(layers.keys())}")
        print(f"Road Distance at center (50, 50): {layers['road_distance'][50, 50]}")
        print(f"Building Mask at center (50, 50): {layers['building_mask'][50, 50]}")
        print(f"Building Height at center (50, 50): {layers['building_height'][50, 50]}")
        
        # Basic assertions to confirm logic is working as expected
        assert layers['road_distance'][50, 50] == 0.0
        assert layers['building_mask'][50, 50] == 1
        assert layers['building_height'][50, 50] == 10.0
        print("\nVerification Successful!")

if __name__ == "__main__":
    verify()
