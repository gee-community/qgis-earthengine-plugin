from unittest.mock import patch

import ee
from qgis.core import QgsProject, QgsPointXY, QgsDataProvider

from ee_plugin import Map
from ee_plugin.provider import EarthEngineRasterDataProvider


def test_raster_identify():
    # Add an image layer to QGIS
    image = ee.Image("USGS/SRTMGL1_003")
    vis_params = {
        "min": 0,
        "max": 4000,
        "palette": ["006633", "E5FFCC", "662A00", "D8D8D8", "F5F5F5"],
    }

    # mocking Map.getScale() was necessary for ee to reproject point correctly
    # simpler than configuring iface and other QGIS objects
    mock_get_scale = patch("ee_plugin.Map.getScale", return_value=625.7583)
    mock_get_scale.start()

    Map.addLayer(image, vis_params, "DEM")

    qgis_instance = QgsProject.instance()
    layer = qgis_instance.mapLayersByName("DEM")[0]
    assert layer is not None, "Layer 'DEM' was not added to the project"
    assert layer.crs().authid() == "EPSG:3857", "Layer CRS does not match project CRS"

    provider = layer.dataProvider()
    qgis_point = QgsPointXY(-13551778.88787266425788403, 5917193.28679858986288309)
    raster_identify_result = provider.identify(
        qgis_point, format=1, height=1, width=1, dpi=96
    )

    assert raster_identify_result, "Identify operation returned no results"
    # can't fetch key to match elevation...
    # but we can verify single band is returned
    # which was an error caused when we modified the ee.Image to the visualize(**params)
    # we simply need to pass visualize(**params) to EarthEngine when creating the WMS URL
    assert (
        raster_identify_result.isValid()
    ), "Identify operation returned an invalid result"
    assert (
        len(raster_identify_result.results()) == 1
    ), "Identify operation returned more than one result, which means multiples bands were returned"
    assert (
        raster_identify_result.results()[1] > 0
    ), "Identified elevation is not positive"


def test_reduce_region():
    ee.Initialize()

    image = ee.Image("USGS/SRTMGL1_003")
    vis_params = {
        "min": 0,
        "max": 4000,
        "palette": ["006633", "E5FFCC", "662A00", "D8D8D8", "F5F5F5"],
    }
    Map.addLayer(image, vis_params, "DEM")
    Map.setCenter(-121.753, 46.855, 9)

    test_point = ee.Geometry.Point([-121.753, 46.855], "EPSG:4326")
    scale = 30  # Scale in meters
    reducer = ee.Reducer.first()
    result = image.reduceRegion(
        reducer=reducer, geometry=test_point, scale=scale
    ).getInfo()

    assert "elevation" in result, {"message": "Elevation not found in result"}
    assert result["elevation"] > 0, {"message": "Elevation is not positive"}


def test_provider_rehydrates_from_asset_id():
    ee.Initialize()

    asset_id = "USGS/SRTMGL1_003"
    image = ee.Image(asset_id)

    provider = EarthEngineRasterDataProvider(
        uri="type=xyz&url=http://example.com",
        providerOptions=QgsDataProvider.ProviderOptions(),
        flags=None,
        image=image,
    )

    # Simulate reload with no ee_object
    provider.asset_id = asset_id
    provider.ee_object = None
    provider.ee_info = None

    provider.set_ee_object_from_asset()

    assert provider.ee_object is not None
    assert provider.ee_info is not None
    assert "bands" in provider.ee_info
