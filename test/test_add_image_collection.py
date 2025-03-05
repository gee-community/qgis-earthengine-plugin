import ee
from qgis.core import QgsMapLayer

from ee_plugin import Map


def test_add_landsat_cloud_cover(clean_qgis_iface):
    collection = (
        ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
        .filterDate("2021-01-01", "2021-12-31")
        .filter(ee.Filter.lt("CLOUD_COVER", 10))
    )
    Map.addLayer(collection, {}, "LANDSAT_2021")
    layers = clean_qgis_iface.mapCanvas().layers()
    assert len(layers) == 1
    assert layers[0]
    layer = layers[0]
    assert layer.name() == "LANDSAT_2021"
    assert layer.type() == QgsMapLayer.RasterLayer
    assert layer.providerType() == "EE"
