from qgis import gui
from PyQt5 import QtWidgets, QtCore

from ee_plugin.ui.utils import get_dialog_values, call_func_with_values
from ee_plugin.ui.forms.add_image_collection import form, callback


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


def test_image_collection_callback(clean_qgis_iface):
    dialog = form()
    dialog.findChild(QtWidgets.QLineEdit, "image_collection_id").setText(
        "LANDSAT/LC09/C02/T1_L2"
    )
    dialog.findChild(QtWidgets.QLineEdit, "filter_name").setText("CLOUD_COVER")
    dialog.findChild(QtWidgets.QComboBox, "filter_operator").setCurrentText(
        "Less Than (<)"
    )
    dialog.findChild(QtWidgets.QLineEdit, "filter_value").setText("10")
    dialog.findChild(gui.QgsDateEdit, "start_date").setDate(QtCore.QDate(2021, 1, 1))
    dialog.findChild(gui.QgsDateEdit, "end_date").setDate(QtCore.QDate(2021, 12, 31))

    call_func_with_values(callback, dialog)

    assert len(clean_qgis_iface.mapCanvas().layers()) == 1
    assert (
        clean_qgis_iface.mapCanvas().layers()[0].name() == "IC: LANDSAT/LC09/C02/T1_L2"
    )
    assert clean_qgis_iface.mapCanvas().layers()[0].dataProvider().name() == "EE"
