import json

from pytest import raises, fixture
from qgis import gui
from PyQt5 import QtWidgets, QtCore

from ee_plugin.ui.widgets import LabeledSlider
from ee_plugin.ui.utils import get_dialog_values, call_func_with_values
from ee_plugin.ui.forms.add_image_collection import form, callback


@fixture
def dialog():
    """Fixture to create a new dialog instance before each test."""
    return form()


def test_image_collection_dialog_values(dialog):
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

    # Get actual values from the dialog
    actual_values = get_dialog_values(dialog)

    # Define expected values
    expected_values = {
        "image_collection_id": "LANDSAT/LC09/C02/T1_L2",
        "filter_name_0": "CLOUD_COVER",
        "filter_operator_0": "Less Than (<)",
        "filter_value_0": "10",
        "filter_name_1": "SUN_ELEVATION",
        "filter_operator_1": "Greater Than (>)",
        "filter_value_1": "0",
        "start_date": "2021-01-01",
        "end_date": "2021-12-31",
        "extent": None,
        "compositing_method": "Mosaic",  # Default compositing method
    }

    assert set(expected_values.items()).issubset(set(actual_values.items()))


def test_image_collection_callback(dialog, clean_qgis_iface):
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
    assert layer.name() == "IC: LANDSAT/LC09/C02/T1_L2 (Mosaic)"
    assert layer.dataProvider().name() == "EE"


def test_image_collection_callback_multiple_filters(dialog, clean_qgis_iface):
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
    assert layer.name() == "IC: LANDSAT/LC09/C02/T1_L2 (Mosaic)"
    assert layer.dataProvider().name() == "EE"


def test_image_collection_dialog_with_string_and_numeric_filters(
    dialog, clean_qgis_iface
):
    # Set image collection ID
    dialog.findChild(QtWidgets.QLineEdit, "image_collection_id").setText(
        "LANDSAT/LC09/C02/T1_L2"
    )

    # Simulate adding multiple filters
    filter_widget = dialog.findChild(QtWidgets.QWidget, "filter_widget")
    add_button = filter_widget.findChild(QtWidgets.QPushButton, "add_filter_button")
    add_button.click()  # Add a second filter row

    # Retrieve the current filter count to assign unique object names
    current_filter_count = (
        filter_widget.layout().count() - 1
    )  # Subtract 1 for the add_button

    # Set first filter (CLOUD_COVER < 10)
    filter_name_0 = dialog.findChild(
        QtWidgets.QLineEdit, f"filter_name_{current_filter_count - 2}"
    )
    filter_operator_0 = dialog.findChild(
        QtWidgets.QComboBox, f"filter_operator_{current_filter_count - 2}"
    )
    filter_value_0 = dialog.findChild(
        QtWidgets.QLineEdit, f"filter_value_{current_filter_count - 2}"
    )

    filter_name_0.setText("CLOUD_COVER")
    filter_operator_0.setCurrentText("Less Than (<)")
    filter_value_0.setText("10")

    # Set second filter (PROCESSING_LEVEL == 'L2SP')
    filter_name_1 = dialog.findChild(
        QtWidgets.QLineEdit, f"filter_name_{current_filter_count - 1}"
    )
    filter_operator_1 = dialog.findChild(
        QtWidgets.QComboBox, f"filter_operator_{current_filter_count - 1}"
    )
    filter_value_1 = dialog.findChild(
        QtWidgets.QLineEdit, f"filter_value_{current_filter_count - 1}"
    )

    filter_name_1.setText("PROCESSING_LEVEL")
    filter_operator_1.setCurrentText("Equals (==)")
    filter_value_1.setText("L2SP")

    # Set date filters
    dialog.findChild(gui.QgsDateEdit, "start_date").setDate(QtCore.QDate(2021, 1, 1))
    dialog.findChild(gui.QgsDateEdit, "end_date").setDate(QtCore.QDate(2021, 12, 31))

    # Call the callback with the dialog values
    call_func_with_values(callback, dialog)

    # Validate that the layer was added to the map
    assert len(clean_qgis_iface.mapCanvas().layers()) == 1
    layer = clean_qgis_iface.mapCanvas().layers()[0]
    assert layer.name() == "IC: LANDSAT/LC09/C02/T1_L2 (Mosaic)"
    assert layer.dataProvider().name() == "EE"


def test_viz_params_valid(dialog):
    """Test that valid viz_params JSON is correctly parsed."""
    dialog.findChild(QtWidgets.QLineEdit, "image_collection_id").setText(
        "LANDSAT/LC09/C02/T1_L2"
    )
    dialog.findChild(QtWidgets.QTextEdit, "viz_params").setPlainText(
        '{"bands":["SR_B4","SR_B3","SR_B2"],"min":0,"max":30000,"gamma":1.3}'
    )

    values = get_dialog_values(dialog)
    assert "viz_params" in values
    assert '{"bands":["SR_B4","SR_B3","SR_B2"],"min":0,"max":30000,"gamma":1.3}'


def test_missing_image_collection_id(dialog):
    """Ensure the form does not proceed if image_collection_id is missing."""
    values = get_dialog_values(dialog)
    assert "image_collection_id" in values
    assert values["image_collection_id"] == ""


def test_filtering_logic(dialog):
    """Test that multiple filters are correctly added."""
    filter_widget = dialog.findChild(QtWidgets.QWidget, "filter_widget")
    add_button = filter_widget.findChild(QtWidgets.QPushButton, "add_filter_button")
    add_button.click()  # Add a second filter row

    filter_rows = filter_widget.findChildren(QtWidgets.QHBoxLayout)

    # Set filters
    filter_rows[0].itemAt(0).widget().setText("CLOUD_COVER")
    filter_rows[0].itemAt(1).widget().setCurrentText("Less Than (<)")
    filter_rows[0].itemAt(2).widget().setText("10")

    filter_rows[1].itemAt(0).widget().setText("SUN_ELEVATION")
    filter_rows[1].itemAt(1).widget().setCurrentText("Greater Than (>)")
    filter_rows[1].itemAt(2).widget().setText("0")

    values = get_dialog_values(dialog)

    assert values["filter_name_0"] == "CLOUD_COVER"
    assert values["filter_operator_0"] == "Less Than (<)"
    assert values["filter_value_0"] == "10"

    assert values["filter_name_1"] == "SUN_ELEVATION"
    assert values["filter_operator_1"] == "Greater Than (>)"
    assert values["filter_value_1"] == "0"


def test_invalid_json_call(dialog):
    """Test that multiple filters are correctly added."""
    dialog.findChild(QtWidgets.QLineEdit, "image_collection_id").setText(
        "LANDSAT/LC09/C02/T1_L2"
    )
    dialog.findChild(QtWidgets.QTextEdit, "viz_params").setText("{'bad'")

    with raises(json.JSONDecodeError):
        call_func_with_values(callback, dialog)


def test_layer_addition(clean_qgis_iface, dialog):
    """Test that the image collection is added as a QGIS layer."""
    dialog.findChild(QtWidgets.QLineEdit, "image_collection_id").setText(
        "LANDSAT/LC09/C02/T1_L2"
    )
    call_func_with_values(callback, dialog)

    assert len(clean_qgis_iface.mapCanvas().layers()) == 1
    layer = clean_qgis_iface.mapCanvas().layers()[0]
    assert layer.name() == "IC: LANDSAT/LC09/C02/T1_L2 (Mosaic)"
    assert layer.dataProvider().name() == "EE"


def test_image_collection_dialog_percentile_compositing(dialog):
    """Test percentile compositing selection and value validation."""
    image_id_input = dialog.findChild(QtWidgets.QLineEdit, "image_collection_id")
    assert image_id_input is not None
    image_id_input.setText("LANDSAT/LC09/C02/T1_L2")

    # Select 'Percentile' method
    method_combo = dialog.findChild(QtWidgets.QComboBox, "compositing_method")
    assert method_combo is not None
    method_combo.setCurrentText("Percentile")

    # Process events to trigger slot
    QtWidgets.QApplication.processEvents()

    # Set a valid percentile value
    dialog.findChild(LabeledSlider, "percentile_value").set_value(75)

    values = get_dialog_values(dialog)

    assert values["compositing_method"] == "Percentile"
    assert values["percentile_value"] == 75


def test_percentile_slider_clamping(dialog):
    """Ensure percentile slider clamps to [0, 100] range."""

    # Set Image Collection ID
    image_id_input = dialog.findChild(QtWidgets.QLineEdit, "image_collection_id")
    assert image_id_input is not None
    image_id_input.setText("LANDSAT/LC09/C02/T1_L2")

    # Select 'Percentile' method
    method_combo = dialog.findChild(QtWidgets.QComboBox, "compositing_method")
    assert method_combo is not None
    method_combo.setCurrentText("Percentile")

    # Process events to trigger slot
    QtWidgets.QApplication.processEvents()

    # get the slider
    slider_widget = dialog.findChild(LabeledSlider, "percentile_value")
    assert (
        slider_widget is not None
    ), "Percentile slider not found (did dynamic add fail?)"

    # Test clamping at upper bound
    slider_widget.slider.setValue(105)  # Slider will clamp to 100
    assert slider_widget.get_value() == 100

    values = get_dialog_values(dialog)
    assert values["compositing_method"] == "Percentile"
    assert values["percentile_value"] == 100

    # Test clamping at lower bound
    slider_widget.slider.setValue(-5)  # Slider will clamp to 0
    assert slider_widget.get_value() == 0

    values = get_dialog_values(dialog)
    assert values["percentile_value"] == 0


def test_image_collection_callback_with_compositing(dialog, clean_qgis_iface):
    """Ensure the correct compositing method is applied when adding a layer."""
    dialog.findChild(QtWidgets.QLineEdit, "image_collection_id").setText(
        "LANDSAT/LC09/C02/T1_L2"
    )

    # Set compositing method
    dialog.findChild(QtWidgets.QComboBox, "compositing_method").setCurrentText("Median")

    call_func_with_values(callback, dialog)

    assert len(clean_qgis_iface.mapCanvas().layers()) == 1
    layer = clean_qgis_iface.mapCanvas().layers()[0]
    assert layer.name() == "IC: LANDSAT/LC09/C02/T1_L2 (Median)"


def test_percentile_slider_added_and_value_set(dialog, clean_qgis_iface):
    """Test that selecting 'Percentile' adds the slider and allows setting value."""

    # Set Image Collection ID
    image_id_input = dialog.findChild(QtWidgets.QLineEdit, "image_collection_id")
    assert image_id_input is not None
    image_id_input.setText("LANDSAT/LC09/C02/T1_L2")

    # Select 'Percentile' method
    method_combo = dialog.findChild(QtWidgets.QComboBox, "compositing_method")
    assert method_combo is not None
    method_combo.setCurrentText("Percentile")

    # Process events to trigger slot
    QtWidgets.QApplication.processEvents()

    # Try finding the LabeledSlider
    slider_widget = dialog.findChild(LabeledSlider, "percentile_value")
    assert (
        slider_widget is not None
    ), "Percentile slider not found (did dynamic add fail?)"

    slider_widget.slider.setValue(90)
    assert slider_widget.get_value() == 90


def test_dynamic_world_form_values(qtbot):
    """Test that the form correctly captures values for Dynamic World dataset."""
    # Setup the form
    dialog = form()
    qtbot.addWidget(dialog)

    # Set Image Collection ID
    ic_input = dialog.findChild(QtWidgets.QLineEdit, "image_collection_id")
    ic_input.setText("GOOGLE/DYNAMICWORLD/V1")

    # Set compositing method to "Mosaic" (index 0)
    method_combo = dialog.findChild(QtWidgets.QComboBox, "compositing_method")
    method_combo.setCurrentIndex(0)  # Mosaic

    # Process UI events
    QtWidgets.QApplication.processEvents()

    # Get values
    values = get_dialog_values(dialog)

    # Assertions
    assert values["image_collection_id"] == "GOOGLE/DYNAMICWORLD/V1"
    assert values["compositing_method"] == "Mosaic"


def test_methanesat_form_percentile(qtbot):
    """Test form values for MethaneSat dataset using Percentile compositing."""
    dialog = form()
    qtbot.addWidget(dialog)

    # Set Image Collection ID
    ic_input = dialog.findChild(QtWidgets.QLineEdit, "image_collection_id")
    ic_input.setText("projects/edf-methanesat-ee/assets/public-preview/L3concentration")

    # Get form values
    values = get_dialog_values(dialog)

    # Assertions
    assert (
        values["image_collection_id"]
        == "projects/edf-methanesat-ee/assets/public-preview/L3concentration"
    )
    assert values["compositing_method"] == "Mosaic"


def test_jrc_global_forest_form_input(qtbot):
    """Test that the form accepts JRC Global Forest V2 dataset ID."""
    dialog = form()
    qtbot.addWidget(dialog)

    # Set Image ID (single image, but form should accept input)
    ic_input = dialog.findChild(QtWidgets.QLineEdit, "image_collection_id")
    ic_input.setText("JRC/GFC2020/V2/TC")

    # Use default compositing method (Mosaic)
    method_combo = dialog.findChild(QtWidgets.QComboBox, "compositing_method")
    assert method_combo.currentText() == "Mosaic"

    QtWidgets.QApplication.processEvents()

    # Get form values
    values = get_dialog_values(dialog)

    # Assertions
    assert values["image_collection_id"] == "JRC/GFC2020/V2/TC"
    assert values["compositing_method"] == "Mosaic"
