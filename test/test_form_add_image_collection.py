from qgis import gui
from PyQt5 import QtWidgets, QtCore

from ee_plugin.ui.utils import get_dialog_values
from ee_plugin.ui.forms.add_image_collection import form


def test_image_collection_dialog_values():
    dialog = form()
    dialog.findChild(QtWidgets.QLineEdit, "image_collection_id").setText(
        "LANDSAT/LC08/C01/T1"
    )
    dialog.findChild(QtWidgets.QLineEdit, "filter_name").setText("CLOUD_COVER")
    dialog.findChild(QtWidgets.QComboBox, "filter_operator").setCurrentText(
        "Less Than (<)"
    )
    dialog.findChild(QtWidgets.QLineEdit, "filter_value").setText("10")
    dialog.findChild(gui.QgsDateEdit, "start_date").setDate(QtCore.QDate(2021, 1, 1))
    dialog.findChild(gui.QgsDateEdit, "end_date").setDate(QtCore.QDate(2021, 12, 31))

    actual_values = get_dialog_values(dialog)
    expected_values = {
        "image_collection_id": "LANDSAT/LC08/C01/T1",
        "filter_name": "CLOUD_COVER",
        "filter_operator": "Less Than (<)",
        "filter_value": "10",
        "start_date": "2021-01-01",
        "end_date": "2021-12-31",
    }
    assert set(expected_values.items()).issubset(actual_values.items())
