import ee
from ee_plugin.utils import get_ee_properties

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
