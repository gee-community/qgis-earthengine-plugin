from qgis.PyQt import QtWidgets

from ee_plugin.ui.utils import get_dialog_values
from ee_plugin.ui.forms.add_ee_image import form, callback


def test_add_gee_layer_dialog(clean_qgis_iface):
    dialog = form()
    dialog.findChild(QtWidgets.QLineEdit, "image_id").setText("COPERNICUS/S2")

    dialog.findChild(QtWidgets.QTextEdit, "viz_params").setText(
        '{"min": 0, "max": 4000, "palette": ["006633", "E5FFCC", "662A00"]}'
    )

    assert get_dialog_values(dialog) == {
        "image_id": "COPERNICUS/S2",
        "viz_params": '{"min": 0, "max": 4000, "palette": ["006633", "E5FFCC", "662A00"]}',
    }


def test_load_gee_layer_srtm(clean_qgis_iface):
    dialog = form()
    dialog.findChild(QtWidgets.QLineEdit, "image_id").setText("USGS/SRTMGL1_003")

    dialog.findChild(QtWidgets.QTextEdit, "viz_params").setText(
        '{"min": 0, "max": 4000, "palette": ["006633", "E5FFCC", "662A00"]}'
    )

    assert get_dialog_values(dialog) == {
        "image_id": "USGS/SRTMGL1_003",
        "viz_params": '{"min": 0, "max": 4000, "palette": ["006633", "E5FFCC", "662A00"]}',
    }

    callback(**get_dialog_values(dialog))

    assert len(clean_qgis_iface.mapCanvas().layers()) == 1
    assert clean_qgis_iface.mapCanvas().layers()[0].name() == "USGS/SRTMGL1_003"
    assert clean_qgis_iface.mapCanvas().layers()[0].dataProvider().name() == "EE"


def test_converting_viz_params_json(clean_qgis_iface):
    dialog = form()
    dialog.findChild(QtWidgets.QLineEdit, "image_id").setText("USGS/SRTMGL1_003")

    # single quotes should get replaced to double quotes
    # by _load_gee_layer, so dialog still has single quotes
    dialog.findChild(QtWidgets.QTextEdit, "viz_params").setText(
        "{'min': 0, 'max': 4000, 'palette': ['006633', 'E5FFCC', '662A00']}"
    )

    callback(**get_dialog_values(dialog))

    assert len(clean_qgis_iface.mapCanvas().layers()) == 1
    assert clean_qgis_iface.mapCanvas().layers()[0].name() == "USGS/SRTMGL1_003"
    assert clean_qgis_iface.mapCanvas().layers()[0].dataProvider().name() == "EE"


def test_invalid_viz_params(clean_qgis_iface):
    dialog = form()
    dialog.findChild(QtWidgets.QLineEdit, "image_id").setText("USGS/SRTMGL1_003")

    dialog.findChild(QtWidgets.QTextEdit, "viz_params").setText(
        "not a valid JSON string"
    )

    callback(**get_dialog_values(dialog))

    assert len(clean_qgis_iface.mapCanvas().layers()) == 0


def test_empty_viz_params(clean_qgis_iface):
    dialog = form()
    dialog.findChild(QtWidgets.QLineEdit, "image_id").setText("USGS/SRTMGL1_003")

    dialog.findChild(QtWidgets.QTextEdit, "viz_params").setText("")

    callback(**get_dialog_values(dialog))

    assert len(clean_qgis_iface.mapCanvas().layers()) == 1
    assert clean_qgis_iface.mapCanvas().layers()[0].name() == "USGS/SRTMGL1_003"
    assert clean_qgis_iface.mapCanvas().layers()[0].dataProvider().name() == "EE"
