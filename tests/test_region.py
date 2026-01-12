import pytest
import numpy as np
from deep_earth.region import RegionContext

def test_invalid_bbox():
    # Latitude out of range
    with pytest.raises(ValueError, match="Invalid latitude"):
        RegionContext(lat_min=-95, lat_max=45, lon_min=-93, lon_max=-92)
    
    # Longitude out of range
    with pytest.raises(ValueError, match="Invalid longitude"):
        RegionContext(lat_min=44, lat_max=45, lon_min=-190, lon_max=-92)
    
    # Min > Max
    with pytest.raises(ValueError, match="must be less than"):
        RegionContext(lat_min=45, lat_max=44, lon_min=-93, lon_max=-92)

def test_utm_zone_detection():
    # Minneapolis (~45N, -93W) should be UTM 15N
    cm = RegionContext(lat_min=44.9, lat_max=45.1, lon_min=-93.1, lon_max=-92.9)
    assert cm.utm_zone == "15N"
    assert cm.utm_epsg == 32615

    # London (~51N, 0W) should be UTM 30N or 31N depending on exact lon
    cm = RegionContext(lat_min=51.4, lat_max=51.6, lon_min=-0.1, lon_max=0.1)
    # Centroid is at 0.0, which is boundary between 30 and 31.
    # WGS84 Lon 0 is the start of zone 31.
    assert cm.utm_zone == "31N"
    assert cm.utm_epsg == 32631

def test_wgs84_to_utm():
    cm = RegionContext(lat_min=44.9, lat_max=45.1, lon_min=-93.1, lon_max=-92.9)
    # Minneapolis center
    lat, lon = 44.9778, -93.2650
    utm_x, utm_y = cm.to_utm(lat, lon)
    
    # Approximate UTM 15N coords for Minneapolis
    assert 470000 < utm_x < 480000
    assert 4980000 < utm_y < 4990000

def test_get_utm_bbox():
    cm = RegionContext(lat_min=44.9, lat_max=45.1, lon_min=-93.1, lon_max=-92.9)
    utm_bbox = cm.get_utm_bbox()
    assert len(utm_bbox) == 4
    # x_min, y_min, x_max, y_max
    x_min, y_min, x_max, y_max = utm_bbox
    assert x_min < x_max
    assert y_min < y_max

def test_region_get_tiles():
    # ~1km x 1km region
    region = RegionContext(45.0, 45.01, 10.0, 10.01)
    
    # Subdivision into ~500m tiles
    tiles = region.get_tiles(tile_size_km=0.5)
    
    assert len(tiles) >= 4
    for tile in tiles:
        assert isinstance(tile, RegionContext)
        assert tile.lat_min >= region.lat_min
        assert tile.lat_max <= region.lat_max
        assert tile.lon_min >= region.lon_min
        assert tile.lon_max <= region.lon_max
