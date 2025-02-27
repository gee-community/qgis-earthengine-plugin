import os

import ee
import numpy as np
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
    dialog.findChild(QtWidgets.QComboBox, "projection").setCurrentIndex(0)
    dialog.findChild(QtWidgets.QSpinBox, "scale").setValue(30)

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


def test_callback_small_region():
    image = ee.Image("USGS/SRTMGL1_003")
    Map.addLayer(image, {}, "DEM")

    extent = (-123.3, 49.0, -122.7, 49.8)
    callback(
        ee_img="DEM",
        extent=extent,
        scale=30,
        projection="EPSG:4326",
        out_path="./test.tif",
    )

    assert os.path.exists("test.tif")
    assert os.path.getsize("test.tif") > 0
    ds = rio.open("test.tif").read(1)
    # test values make sens for elevation in region
    assert np.nanmean(ds) > 0
    assert np.nanmean(ds) < 1000
    # TODO: remove file
