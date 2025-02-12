from qgis.PyQt import QtWidgets

from ee_plugin.ui.utils import get_values
from ee_plugin.ui.form_add_ee_image import add_gee_layer_dialog, _load_gee_layer


def test_add_gee_layer_dialog(qgis_iface_clean):
    dialog = add_gee_layer_dialog(qgis_iface_clean)
    dialog.findChild(QtWidgets.QLineEdit, "datasetId").setText("COPERNICUS/S2")

    dialog.findChild(QtWidgets.QTextEdit, "vizParams").setText(
        '{"min": 0, "max": 4000, "palette": ["006633", "E5FFCC", "662A00"]}'
    )

    assert get_values(dialog) == {
        "datasetId": "COPERNICUS/S2",
        "vizParams": '{"min": 0, "max": 4000, "palette": ["006633", "E5FFCC", "662A00"]}',
    }


def test_load_gee_layer_srtm(qgis_iface_clean):
    dialog = add_gee_layer_dialog(qgis_iface_clean)
    dialog.findChild(QtWidgets.QLineEdit, "datasetId").setText("USGS/SRTMGL1_003")

    dialog.findChild(QtWidgets.QTextEdit, "vizParams").setText(
        '{"min": 0, "max": 4000, "palette": ["006633", "E5FFCC", "662A00"]}'
    )

    assert get_values(dialog) == {
        "datasetId": "USGS/SRTMGL1_003",
        "vizParams": '{"min": 0, "max": 4000, "palette": ["006633", "E5FFCC", "662A00"]}',
    }

    _load_gee_layer(dialog)

    assert len(qgis_iface_clean.mapCanvas().layers()) == 1
    assert qgis_iface_clean.mapCanvas().layers()[0].name() == "USGS/SRTMGL1_003"
    assert qgis_iface_clean.mapCanvas().layers()[0].dataProvider().name() == "EE"


def test_converting_viz_params_json(qgis_iface_clean):
    dialog = add_gee_layer_dialog(qgis_iface_clean)
    dialog.findChild(QtWidgets.QLineEdit, "datasetId").setText("USGS/SRTMGL1_003")

    # single quotes should get replaced to double quotes
    # by _load_gee_layer, so dialog still has single quotes
    dialog.findChild(QtWidgets.QTextEdit, "vizParams").setText(
        "{'min': 0, 'max': 4000, 'palette': ['006633', 'E5FFCC', '662A00']}"
    )

    _load_gee_layer(dialog)

    assert len(qgis_iface_clean.mapCanvas().layers()) == 1
    assert qgis_iface_clean.mapCanvas().layers()[0].name() == "USGS/SRTMGL1_003"
    assert qgis_iface_clean.mapCanvas().layers()[0].dataProvider().name() == "EE"


def test_invalid_vis_params(qgis_iface_clean):
    dialog = add_gee_layer_dialog(qgis_iface_clean)
    dialog.findChild(QtWidgets.QLineEdit, "datasetId").setText("USGS/SRTMGL1_003")

    dialog.findChild(QtWidgets.QTextEdit, "vizParams").setText(
        "not a valid JSON string"
    )

    _load_gee_layer(dialog)

    assert len(qgis_iface_clean.mapCanvas().layers()) == 0
