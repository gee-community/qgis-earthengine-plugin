import ee
import pytest
from qgis.core import QgsMapLayer, QgsProject

from ee_plugin import Map

# initialize the Earth Engine API is required to use the ee.Geometry module
#   and runs before fixtures
ee.Initialize()

geometries = [
    (ee.Geometry.Point([1.5, 1.5]), {"color": "1eff05"}, "point"),
    (
        ee.Geometry.LineString([[-35, -10], [35, -10], [35, 10], [-35, 10]]),
        {"color": "FF0000"},
        "lineString",
    ),
    (
        ee.Geometry.LinearRing(
            [[-35, -10], [35, -10], [35, 10], [-35, 10], [-35, -10]]
        ),
        {"color": "ee38ff"},
        "linearRing",
    ),
    (ee.Geometry.Rectangle([-40, -20, 40, 20]), {"color": "ffa05c"}, "rectangle"),
    (
        ee.Geometry.Polygon([[[-5, 40], [65, 40], [65, 60], [-5, 60], [-5, 40]]]),
        {"color": "FF0000"},
        "geodesic polygon",
    ),
    (
        ee.Geometry(
            ee.Geometry.Polygon([[[-5, 40], [65, 40], [65, 60], [-5, 60], [-5, 40]]]),
            None,
            False,
        ),
        {"color": "000000"},
        "planar polygon",
    ),
]


@pytest.mark.parametrize("geometry, vis_params, layer_name", geometries)
def test_add_geometry_layer(geometry, vis_params, layer_name):
    qgis_instance = QgsProject.instance()
    Map.addLayer(geometry, vis_params, layer_name)

    layers = qgis_instance.mapLayersByName(layerName=layer_name)
    assert len(layers) == 1, "Wrong number of layers added"

    layer = layers[0]
    assert layer, "Layer not found"
    assert layer.name() == layer_name, "Layer name mismatch"
    assert layer.type() == QgsMapLayer.VectorLayer, "Layer is not a vector layer"


def test_data_catalog_vector_layer():
    qgis_instance = QgsProject.instance()

    ecoregions = ee.FeatureCollection("RESOLVE/ECOREGIONS/2017")

    Map.addLayer(ecoregions, {}, "ecoregions")

    layers = qgis_instance.mapLayersByName(layerName="ecoregions")
    assert len(layers) == 1, "Wrong number of layers added"
    assert layers[0].name() == "ecoregions", "Layer name mismatch"
    assert (
        layers[0].type() == QgsMapLayer.RasterLayer
    ), "Layer is treated as raster layer"
