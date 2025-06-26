import pytest
from qgis.core import QgsRectangle

import ee
from ee_plugin.utils import get_ee_properties, get_available_bands, tile_extent

# Initialize Earth Engine
ee.Initialize()


def test_get_properties_from_image_collection():
    asset_id = "COPERNICUS/S2_HARMONIZED"
    props = get_ee_properties(asset_id)
    assert isinstance(props, list)
    assert len(props) > 0
    assert "CLOUDY_PIXEL_PERCENTAGE" in props


def test_get_properties_from_feature_collection():
    asset_id = "USDOS/LSIB_SIMPLE/2017"
    props = get_ee_properties(asset_id)
    assert isinstance(props, list)
    assert len(props) > 0
    assert "country_na" in props or "wld_rgn" in props


def test_get_properties_from_image():
    asset_id = "USGS/SRTMGL1_003"
    props = get_ee_properties(asset_id)
    assert isinstance(props, list)
    len(props) > 0
    assert "date_range"


def test_invalid_asset_returns_none():
    asset_id = "FAKE/INVALID/ASSET"
    props = get_ee_properties(asset_id)
    assert props is None


def test_get_available_bands():
    asset_id = "COPERNICUS/S2_HARMONIZED"
    bands = get_available_bands(asset_id)
    assert isinstance(bands, list)
    assert len(bands) > 0
    assert "B1" in bands or "B2" in bands


def test_get_available_bands_landsat():
    asset_id = "LANDSAT/LC09/C02/T1_L2"
    bands = get_available_bands(asset_id)
    assert isinstance(bands, list)
    print(bands)
    assert len(bands) > 0
    assert "SR_B1" in bands or "SR_B2" in bands


@pytest.mark.timeout(5)
def test_tile_extent_coordinates_match_projection():
    # Test with a known image
    img = ee.Image("USGS/SRTMGL1_003")
    extent_3857 = QgsRectangle(-13700000, 6300000, -13680000, 6320000)

    with pytest.raises(ValueError):
        # This should raise an error if the projection is not EPSG:4326
        tile_extent(
            img, extent_3857.toRectF().getCoords(), scale=30, projection="EPSG:4326"
        )
