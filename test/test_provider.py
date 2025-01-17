import ee
from qgis.core import QgsProject, QgsPointXY

from ee_plugin import Map


def test_point_identify():
    point = ee.Geometry.Point([1.5, 1.5])
    Map.addLayer(point, {"color": "1eff05"}, "point_layer")

    layer = QgsProject.instance().mapLayersByName("point_layer")[0]
    assert layer is not None, "Layer 'point_layer' was not added to the project"

    provider = layer.dataProvider()
    result = provider.identify(QgsPointXY(1.5, 1.5), QgsProject.instance().crs(), 0.1)
    assert result, "Identify operation returned no results"

    assert len(result) > 0, "Identify operation returned an empty result set"
    geometry = result[0].geometry()
    assert geometry is not None, "Geometry of identified feature is None"
    assert not geometry.asPoint().isNull(), "Identified point is invalid (0, 0)"
