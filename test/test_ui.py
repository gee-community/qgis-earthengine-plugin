import datetime
from unittest.mock import create_autospec

import pytest
from ee_plugin.ui.forms import add_feature_collection
from qgis import gui
from qgis.PyQt import QtWidgets, QtGui
from ee_plugin.ui import utils


def test_get_values():
    dialog = utils.build_vbox_dialog(
        widgets=[
            utils.build_form_group_box(
                rows=[
                    (
                        "Label",
                        QtWidgets.QLineEdit(objectName="line_edit"),
                    ),
                    (
                        "Check",
                        QtWidgets.QCheckBox(objectName="check_box"),
                    ),
                ],
            ),
        ],
    )
    dialog.show()

    dialog.findChild(QtWidgets.QLineEdit, "line_edit").setText("test")
    dialog.findChild(QtWidgets.QCheckBox, "check_box").setChecked(True)

    assert utils.get_dialog_values(dialog) == {
        "line_edit": "test",
        "check_box": True,
    }


@pytest.mark.parametrize(
    "form_input,expected_form_output",
    [
        (
            {
                "feature_collection_id": "USGS/WBD/2017/HUC06",
            },
            {
                "feature_collection_id": "USGS/WBD/2017/HUC06",
            },
        ),
        (
            {
                "feature_collection_id": "USGS/WBD/2017/HUC06",
                "start_date": (gui.QgsDateEdit, "2020-01-01"),
                "end_date": (gui.QgsDateEdit, "2020-12-31"),
            },
            {
                "feature_collection_id": "USGS/WBD/2017/HUC06",
                "start_date": "2020-01-01",
                "end_date": "2020-12-31",
            },
        ),
        (
            {
                "feature_collection_id": "USGS/WBD/2017/HUC06",
                "start_date": (gui.QgsDateEdit, "2020-01-01"),
                "end_date": (gui.QgsDateEdit, "2020-12-31"),
            },
            {
                "feature_collection_id": "USGS/WBD/2017/HUC06",
                "start_date": "2020-01-01",
                "end_date": "2020-12-31",
            },
        ),
        (
            {
                "feature_collection_id": "USGS/WBD/2017/HUC06",
                "viz_color_hex": (gui.QgsColorButton, "#F00"),
            },
            {
                "feature_collection_id": "USGS/WBD/2017/HUC06",
                "viz_color_hex": "#ff0000",
            },
        ),
    ],
)
def test_add_feature_collection_form(qgis_iface, form_input, expected_form_output):
    mock_callback = create_autospec(add_feature_collection.callback)
    dialog = add_feature_collection.form(iface=qgis_iface, accepted=mock_callback)

    # Populate dialog with form_input
    for key, value in form_input.items():
        if isinstance(value, tuple):
            widget_cls, value = value
        else:
            widget_cls = QtWidgets.QWidget

        widget = dialog.findChild(widget_cls, key)

        if isinstance(widget, gui.QgsDateEdit):
            widget.setDate(datetime.datetime.strptime(value, "%Y-%m-%d").date())
        elif isinstance(widget, gui.QgsColorButton):
            widget.setColor(QtGui.QColor(value))
        else:
            widget.setText(value)

    dialog.accept()

    default_outputs = {
        "filter_name": "",
        "filter_value": "",
        "start_date": None,
        "end_date": None,
        "extent": None,
        "viz_color_hex": "#000000",
        "as_vector": False,
    }

    mock_callback.assert_called_once_with(**{**default_outputs, **expected_form_output})


def test_callback(qgis_iface):
    add_feature_collection.callback(
        feature_collection_id="USGS/WBD/2017/HUC06",
        filter_name=None,
        filter_value=None,
        start_date=None,
        end_date=None,
        extent=None,
        viz_color_hex="#000000",
        as_vector=False,
    )

    assert len(qgis_iface.mapCanvas().layers()) == 1
    assert qgis_iface.mapCanvas().layers()[0].name() == "FC: SGS/WBD/2017/HUC06"
    assert qgis_iface.mapCanvas().layers()[0].dataProvider().name() == "EE"
