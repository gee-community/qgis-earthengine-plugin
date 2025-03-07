from qgis import gui
from PyQt5 import QtWidgets, QtCore

from ee_plugin.ui.utils import get_dialog_values, call_func_with_values
from ee_plugin.ui.forms.add_image_collection import form, callback


def test_image_collection_dialog_values():
    dialog = form()

    # Set image collection ID
    dialog.findChild(QtWidgets.QLineEdit, "image_collection_id").setText(
        "LANDSAT/LC08/C01/T1"
    )

    # Simulate adding multiple filters
    filter_widget = dialog.findChild(QtWidgets.QWidget, "filter_widget")
    add_button = filter_widget.findChild(QtWidgets.QPushButton, "add_filter_button")
    add_button.click()  # Add a second filter row

    # Find filter rows
    filter_rows = filter_widget.findChildren(QtWidgets.QHBoxLayout)

    # Set first filter (CLOUD_COVER < 10)
    filter_rows[0].itemAt(0).widget().setText("CLOUD_COVER")
    filter_rows[0].itemAt(1).widget().setCurrentText("Less Than (<)")
    filter_rows[0].itemAt(2).widget().setText("10")

    # Set second filter (SUN_ELEVATION > 0)
    filter_rows[1].itemAt(0).widget().setText("SUN_ELEVATION")
    filter_rows[1].itemAt(1).widget().setCurrentText("Greater Than (>)")
    filter_rows[1].itemAt(2).widget().setText("0")

    # Set date filters
    dialog.findChild(gui.QgsDateEdit, "start_date").setDate(QtCore.QDate(2021, 1, 1))
    dialog.findChild(gui.QgsDateEdit, "end_date").setDate(QtCore.QDate(2021, 12, 31))

    # Get actual values from the dialog
    actual_values = get_dialog_values(dialog)

    # Define expected values
    expected_values = {
        "image_collection_id": "LANDSAT/LC08/C01/T1",
        "filter_name_0": "CLOUD_COVER",
        "filter_operator_0": "Less Than (<)",
        "filter_value_0": "10",
        "filter_name_1": "SUN_ELEVATION",
        "filter_operator_1": "Greater Than (>)",
        "filter_value_1": "0",
        "start_date": "2021-01-01",
        "end_date": "2021-12-31",
        "extent": None,
    }

    assert set(expected_values.items()).issubset(set(actual_values.items()))


def test_image_collection_callback(clean_qgis_iface):
    dialog = form()

    # Set image collection ID
    dialog.findChild(QtWidgets.QLineEdit, "image_collection_id").setText(
        "LANDSAT/LC09/C02/T1_L2"
    )

    # Simulate adding a single filter
    filter_widget = dialog.findChild(QtWidgets.QWidget, "filter_widget")
    filter_rows = filter_widget.findChildren(QtWidgets.QHBoxLayout)

    # Set filter (CLOUD_COVER < 10)
    filter_rows[0].itemAt(0).widget().setText("CLOUD_COVER")
    filter_rows[0].itemAt(1).widget().setCurrentText("Less Than (<)")
    filter_rows[0].itemAt(2).widget().setText("10")

    # Set date filters
    dialog.findChild(gui.QgsDateEdit, "start_date").setDate(QtCore.QDate(2021, 1, 1))
    dialog.findChild(gui.QgsDateEdit, "end_date").setDate(QtCore.QDate(2021, 12, 31))

    # Call the callback with the dialog values
    call_func_with_values(callback, dialog)

    # Validate that the layer was added to the map
    assert len(clean_qgis_iface.mapCanvas().layers()) == 1
    layer = clean_qgis_iface.mapCanvas().layers()[0]
    assert layer.name() == "IC: LANDSAT/LC09/C02/T1_L2"
    assert layer.dataProvider().name() == "EE"


def test_image_collection_callback_multiple_filters(clean_qgis_iface):
    dialog = form()

    # Set image collection ID
    dialog.findChild(QtWidgets.QLineEdit, "image_collection_id").setText(
        "LANDSAT/LC09/C02/T1_L2"
    )

    # Simulate adding multiple filters
    filter_widget = dialog.findChild(QtWidgets.QWidget, "filter_widget")
    add_button = filter_widget.findChild(QtWidgets.QPushButton, "add_filter_button")
    add_button.click()  # Add a second filter row

    # Find filter rows
    filter_rows = filter_widget.findChildren(QtWidgets.QHBoxLayout)

    # Set first filter (CLOUD_COVER < 10)
    filter_rows[0].itemAt(0).widget().setText("CLOUD_COVER")
    filter_rows[0].itemAt(1).widget().setCurrentText("Less Than (<)")
    filter_rows[0].itemAt(2).widget().setText("10")

    # Set second filter (SUN_ELEVATION > 0)
    filter_rows[1].itemAt(0).widget().setText("SUN_ELEVATION")
    filter_rows[1].itemAt(1).widget().setCurrentText("Greater Than (>)")
    filter_rows[1].itemAt(2).widget().setText("0")

    # Set date filters
    dialog.findChild(gui.QgsDateEdit, "start_date").setDate(QtCore.QDate(2021, 1, 1))
    dialog.findChild(gui.QgsDateEdit, "end_date").setDate(QtCore.QDate(2021, 12, 31))

    # Call the callback with the dialog values
    call_func_with_values(callback, dialog)

    # Validate that the layer was added to the map
    assert len(clean_qgis_iface.mapCanvas().layers()) == 1
    layer = clean_qgis_iface.mapCanvas().layers()[0]
    assert layer.name() == "IC: LANDSAT/LC09/C02/T1_L2"
    assert layer.dataProvider().name() == "EE"
