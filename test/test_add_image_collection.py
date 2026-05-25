import ee
from qgis.core import QgsMapLayer

from ee_plugin import Map
from ee_plugin.utils import get_layer_by_name


def test_add_landsat_cloud_cover(clean_qgis_iface):
    collection = (
        ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
        .filterDate("2021-01-01", "2021-12-31")
        .filter(ee.Filter.lt("CLOUD_COVER", 10))
    )
    Map.addLayer(collection, {}, "LANDSAT_2021")
    layer = get_layer_by_name("LANDSAT_2021")
    assert layer is not None
    assert layer.name() == "LANDSAT_2021"
    assert layer.type() == QgsMapLayer.LayerType.RasterLayer
    assert layer.customProperty("ee-layer")
    assert layer.customProperty("ee-layer-type") == "raster"
