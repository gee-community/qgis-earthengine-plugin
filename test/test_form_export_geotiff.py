import os
import time

import ee
import pytest
import rasterio as rio
from qgis.PyQt import QtWidgets

from ee_plugin import Map
from ee_plugin.ui.utils import get_dialog_values
from ee_plugin.utils import tile_extent
from ee_plugin.ui.forms.export_geotiff import form, callback


def test_export_dialog_values():
    image = ee.Image("USGS/SRTMGL1_003")
    Map.addLayer(image, {}, "DEM")
    dialog = form()
    dialog.findChild(QtWidgets.QWidget, "out_path").findChild(
        QtWidgets.QLineEdit
    ).setText("test.tif")
    dialog.findChild(QtWidgets.QComboBox, "ee_img").setCurrentIndex(0)
    dialog.findChild(QtWidgets.QDoubleSpinBox, "scale").setValue(30)

    exp_values = {
        "ee_img": "DEM",
        "extent": None,
        "projection": "EPSG:4326",
        "scale": 30,
        "out_path": "test.tif",
    }
    print(exp_values)
    print(get_dialog_values(dialog))

    ## expected values is a subset of the dialog values
    assert exp_values.items() <= get_dialog_values(dialog).items()


def test_callback_layer_not_found():
    callback(
        ee_img="non_existent",
        extent=None,
        scale=1000,
        projection="EPSG:4326",
        out_path="test.tif",
    )

    assert not os.path.exists("test.tif")


# quotas on EE can be exceeded
# using very low scale for large extents
@pytest.mark.parametrize(
    "crs, scale, extent",
    [
        ("EPSG:4326", 1000, (-123.5, 49.5, -122.5, 50.5)),  # WGS 84, small scale
        ("EPSG:4326", 10000, None),  # WGS 84, auto extent
        ("EPSG:3857", 1000, (-13733500, 6305000, -13675000, 6420000)),  # Web Mercator
        ("EPSG:3857", 10000, None),  # Web Mercator, auto extent
        ("EPSG:32610", 1000, (500000, 5475000, 600000, 5575000)),  # UTM Zone 10N
        ("EPSG:32610", 10000, None),  # UTM, auto extent
    ],
)
def test_callback_varied_params(crs, scale, extent):
    time.sleep(1)  # connection pool can get full
    image = ee.Image("USGS/SRTMGL1_003")
    Map.addLayer(image, {}, "DEM")

    out_path = f"test_{crs}_{scale}.tif"

    callback(
        ee_img="DEM",
        extent=extent,
        scale=scale,
        projection=crs,
        out_path=out_path,
    )

    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0

    with rio.open(out_path) as ds:
        assert ds.count == 1, "Unexpected number of bands"
        assert ds.width > 0 and ds.height > 0, "Invalid raster size"

    # os.remove(out_path)


@pytest.mark.parametrize(
    "extent, scale, max_pixels, expected_tiles",
    [
        # Case 1: No tiling needed (within limit)
        ((0, 0, 100, 100), 1, 200, 1),  # 100x100 pixels = under limit
        # Case 2: Tiling required in X only
        ((0, 0, 400, 100), 1, 200, 2),  # 400x100 pixels → 2 tiles in X
        # Case 3: Tiling required in Y only
        ((0, 0, 100, 500), 1, 200, 3),  # 100x500 pixels → 3 tiles in Y
        # Case 4: Tiling in both X and Y
        ((0, 0, 500, 500), 1, 200, 9),  # 500x500 pixels → 3x3 tiles
        # Case 5: Very large extent with small scale
        ((0, 0, 1000, 1000), 0.1, 32768, 1),  # 10,000x10,000 pixels → under EE limit
        # Case 6: Edge case - exactly at max pixels
        ((0, 0, 32768, 32768), 1, 32768, 1),  # Exactly 32768 pixels each side
        # Case 7: Just over max pixels
        ((0, 0, 40000, 40000), 1, 32768, 4),  # 40000x40000 pixels → 2x2 tiles
    ],
)
def test_tile_extent(extent, scale, max_pixels, expected_tiles):
    tiles = tile_extent(extent, scale, max_pixels)
    assert (
        len(tiles) == expected_tiles
    ), f"Expected {expected_tiles} tiles, got {len(tiles)}"


def test_tile_extent_pixel_limit_trigger():
    # Create 100,000 x 100,000 pixels → triggers tiling
    extent = (-123.5, 49.5, 876.5, 1049.5)  # 1000° x 1000°
    scale = 0.01
    max_pixels = 32768

    tiles = tile_extent(extent, scale, max_pixels)

    assert len(tiles) > 1, f"Expected tiling, got {len(tiles)} tile(s)"
