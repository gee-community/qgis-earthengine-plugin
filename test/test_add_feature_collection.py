def test_add_feature_collection_algorithm_retain_vector(clean_qgis_iface):
    from ee_plugin.processing.add_feature_collection import (
        AddFeatureCollectionAlgorithm,
    )
    from qgis.core import QgsProcessingContext, QgsProcessingFeedback

    algorithm = AddFeatureCollectionAlgorithm()
    algorithm.initAlgorithm(config=None)

    parameters = {
        "feature_collection_id": "USGS/WBD/2017/HUC06",
        "filters": "states:==:FL,GA",  # limits to 3 features
        "start_date": "2020-01-01",
        "end_date": "2020-12-31",
        "extent": "-180,-90 : 180,90",
        "opacity": "100",
        "viz_color_hex": "#000000",
        "viz_fill_color": "#ffffff",
        "viz_width": "2",
        "as_vector": "True",
    }

    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()
    result = algorithm.processAlgorithm(parameters, context, feedback)

    assert isinstance(result, dict)
    assert "OUTPUT_VECTOR" in result
    try:
        layer = clean_qgis_iface.mapCanvas().layers()[0]
    except IndexError:
        assert False, "No layers found in the map canvas."
    assert layer is not None
    assert layer.name() == "FC: USGS/WBD/2017/HUC06"
    assert layer.featureCount() > 0
    assert layer.providerType() == "ogr"


def test_add_feature_collection_algorithm(clean_qgis_iface):
    from ee_plugin.processing.add_feature_collection import (
        AddFeatureCollectionAlgorithm,
    )
    from qgis.core import QgsProcessingContext, QgsProcessingFeedback

    algorithm = AddFeatureCollectionAlgorithm()
    algorithm.initAlgorithm(config=None)

    parameters = {
        "feature_collection_id": "USGS/WBD/2017/HUC06",
        "filters": "states:==:FL,GA",
        "start_date": "2020-01-01",
        "end_date": "2020-12-31",
        "extent": "-180,-90 : 180,90",
        "opacity": "100",
        "viz_color_hex": "#000000",
        "viz_fill_color": "#ffffff",
        "viz_width": "2",
        "as_vector": "False",
    }

    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()
    result = algorithm.processAlgorithm(parameters, context, feedback)

    assert isinstance(result, dict)
    assert "OUTPUT_RASTER" in result
    try:
        layer = clean_qgis_iface.mapCanvas().layers()[0]
    except IndexError:
        assert False, "No layers found in the map canvas."
    assert layer is not None
    assert layer.name() == "FC: USGS/WBD/2017/HUC06"
    assert layer.providerType() == "EE"
