import os
import time

import ee
import pytest
import rasterio as rio
from qgis.PyQt import QtWidgets

from ee_plugin import Map
from ee_plugin.ui.utils import get_dialog_values
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
        ("EPSG:4326", 0.01, (-123.5, 49.5, -122.5, 50.5)),  # WGS 84, small scale
        ("EPSG:4326", 40, None),  # WGS 84, auto extent
        ("EPSG:3857", 1000, (-13733500, 6305000, -13675000, 6420000)),  # Web Mercator
        ("EPSG:3857", 10000000, None),  # Web Mercator, auto extent
        ("EPSG:32610", 1000, (500000, 5475000, 600000, 5575000)),  # UTM Zone 10N
        ("EPSG:32610", 10000000, None),  # UTM, auto extent
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

    os.remove(out_path)
