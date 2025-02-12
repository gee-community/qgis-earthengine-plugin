from qgis.PyQt import QtWidgets
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

    assert utils.get_values(dialog) == {
        "line_edit": "test",
        "check_box": True,
    }


def test_add_feature_collection_form(qgis_iface):
    dialog = forms.add_feature_collection_form(iface=qgis_iface)

    dialog.findChild(QtWidgets.QLineEdit, "feature_collection_id").setText(
        "USGS/WBD/2017/HUC06"
    )

    assert utils.get_values(dialog) == {
        "feature_collection_id": "USGS/WBD/2017/HUC06",
        "filter_name": "",
        "filter_value": "",
        # "start_date": "",  # TODO: This is missing
        # "end_date": "",  # TODO: This is missing
        "mYMaxLineEdit": "",
        "mYMinLineEdit": "",
        "mXMaxLineEdit": "",
        "mXMinLineEdit": "",
        "viz_color_hex": "#000000",
        "use_util": False,
        **{  # TODO: this is unexpected
            "mCondensedLineEdit": "",
            "qt_spinbox_lineedit": "2025-02-12",
        },
    }
