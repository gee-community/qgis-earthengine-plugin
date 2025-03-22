from qgis.core import (
    QgsProcessingContext,
    QgsProcessingFeedback,
)
from ee_plugin.processing.add_ee_image import AddEEImageAlgorithm


def run_algorithm_with_params(params):
    alg = AddEEImageAlgorithm()
    alg.initAlgorithm()
    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()
    return alg.processAlgorithm(params, context, feedback)


def test_add_gee_layer_algorithm(clean_qgis_iface):
    params = {
        "IMAGE_ID": "USGS/SRTMGL1_003",
        "VIZ_PARAMS": '{"min": 0, "max": 3000, "palette": ["#000000", "#ffffff"]}',
    }
    run_algorithm_with_params(params)
    layer = clean_qgis_iface.mapCanvas().layers()[0]
    assert layer.name() == "USGS/SRTMGL1_003"
    assert layer.dataProvider().name() == "EE"


def test_load_gee_layer_srtm(clean_qgis_iface):
    params = {
        "IMAGE_ID": "USGS/SRTMGL1_003",
        "VIZ_PARAMS": '{"min": 0, "max": 4000, "palette": ["006633", "E5FFCC", "662A00"]}',
    }
    run_algorithm_with_params(params)
    layer = clean_qgis_iface.mapCanvas().layers()[0]
    assert layer.name() == "USGS/SRTMGL1_003"
    assert layer.dataProvider().name() == "EE"


def test_converting_viz_params_json(clean_qgis_iface):
    params = {
        "IMAGE_ID": "USGS/SRTMGL1_003",
        "VIZ_PARAMS": "{'min': 0, 'max': 4000, 'palette': ['006633', 'E5FFCC', '662A00']}",
    }
    run_algorithm_with_params(params)
    layer = clean_qgis_iface.mapCanvas().layers()[0]
    assert layer.name() == "USGS/SRTMGL1_003"
    assert layer.dataProvider().name() == "EE"


def test_invalid_viz_params(clean_qgis_iface):
    params = {
        "IMAGE_ID": "USGS/SRTMGL1_003",
        "VIZ_PARAMS": "not a valid JSON string",
    }
    try:
        run_algorithm_with_params(params)
    except Exception:
        pass
    assert len(clean_qgis_iface.mapCanvas().layers()) == 0


def test_empty_viz_params(clean_qgis_iface):
    params = {
        "IMAGE_ID": "USGS/SRTMGL1_003",
        "VIZ_PARAMS": "",
    }
    run_algorithm_with_params(params)
    layer = clean_qgis_iface.mapCanvas().layers()[0]
    assert layer.name() == "USGS/SRTMGL1_003"
    assert layer.dataProvider().name() == "EE"
