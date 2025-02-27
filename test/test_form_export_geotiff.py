import ee
from qgis.PyQt import QtWidgets

from ee_plugin import Map
from ee_plugin.ui.utils import get_dialog_values
from ee_plugin.ui.forms.export_geotiff import form


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
