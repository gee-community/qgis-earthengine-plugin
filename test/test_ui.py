import datetime
from unittest.mock import create_autospec

import pytest
from qgis import gui
from qgis.PyQt import QtWidgets, QtGui
from ee_plugin.ui import utils, forms


def test_get_values():
    dialog = forms.build_vbox_dialog(
        widgets=[
            forms.build_form_group_box(
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
    callback = create_autospec(forms.add_feature_collection)
    dialog = forms.add_feature_collection_form(iface=qgis_iface, accepted=callback)

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

    callback.assert_called_once_with(**{**default_outputs, **expected_form_output})
