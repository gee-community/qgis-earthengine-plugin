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


def test_raster_identify():
    image = ee.Image("USGS/SRTMGL1_003")
    vis_params = {
        "min": 0,
        "max": 4000,
        "palette": ["006633", "E5FFCC", "662A00", "D8D8D8", "F5F5F5"],
    }
    Map.addLayer(image, vis_params, "DEM")

    layer = QgsProject.instance().mapLayersByName("DEM")[0]
    assert layer is not None, "Layer 'DEM' was not added to the project"

    provider = layer.dataProvider()
    assert provider is not None, "Provider for the layer could not be retrieved"

    point = QgsPointXY(
        -13553481.96255343593657017, 5907008.49828365817666054
    )  # Example point in WGS84

    result = provider.identify(
        point, format=None, boundingBox=None, width=None, height=None
    )
    print("Identify result:", result.results())
    assert result, "Identify operation returned no results"
    assert len(result.results()) > 0, "Identify operation returned an empty result set"
