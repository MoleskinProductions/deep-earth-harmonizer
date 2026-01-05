import numpy as np
from deep_earth.harmonize import Harmonizer
from deep_earth.coordinates import CoordinateManager

def verify():
    # 1. Setup Coordinate Manager
    print("Initializing Coordinate Manager...")
    cm = CoordinateManager(lat_min=45.0, lat_max=45.01, lon_min=-93.0, lon_max=-92.99)
    
    # 2. Setup Harmonizer
    print("Initializing Harmonizer...")
    h = Harmonizer(cm, resolution=10)
    print(f"Master Grid Dimensions: {h.width}x{h.height}")
    
    # 3. Simulate OSM Layer Integration
    print("Simulating OSM layer integration...")
    layers = {
        'test_osm_road_dist': np.ones((h.height, h.width), dtype=np.float32),
        'test_osm_building_mask': np.zeros((h.height, h.width), dtype=np.uint8)
    }
    
    h.add_layers(layers)
    
    # 4. Verify
    print(f"Integrated Layers: {list(h.layers.keys())}")
    expected_sum = h.width * h.height
    actual_sum = np.sum(h.layers['test_osm_road_dist'])
    
    print(f"Expected Sum: {expected_sum}")
    print(f"Actual Sum:   {actual_sum}")
    
    assert 'test_osm_road_dist' in h.layers
    assert h.layers['test_osm_road_dist'].shape == (h.height, h.width)
    assert actual_sum == expected_sum
    
    print("\nVerification Successful! Harmonizer correctly accepts and validates external layers.")

if __name__ == "__main__":
    verify()
