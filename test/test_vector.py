import ee
from ee_plugin import Map


def test_add_point_layer():
    point = ee.Geometry.Point([1.5, 1.5])
    Map.addLayer(point, {"color": "1eff05"}, "point")
