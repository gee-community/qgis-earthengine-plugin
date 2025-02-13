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

    dialog_values = utils.get_values(dialog)

    assert (
        dialog_values.items()
        >= {
            "feature_collection_id": "USGS/WBD/2017/HUC06",
            "filter_name": "",
            "filter_value": "",
            "start_date": None,
            "end_date": None,
            "extent": None,
            "viz_color_hex": "#000000",
            "use_util": False,
        }.items()
    )
