import pytest

from qgis.PyQt.QtCore import QDateTime
from qgis.core import (
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsRectangle,
    QgsCoordinateReferenceSystem,
)

from ee_plugin.processing.add_image_collection import AddImageCollectionAlgorithm


def run_algorithm_with_params(params):
    alg = AddImageCollectionAlgorithm()
    alg.initAlgorithm(config=None)
    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()
    return alg.processAlgorithm(params, context, feedback)


def test_add_image_collection_algorithm_with_filters(clean_qgis_iface):
    start_date = QDateTime(2021, 1, 1, 12, 0, 0)  # Pass QDateTime object
    end_date = QDateTime(2021, 12, 31, 12, 0, 0)  # Pass QDateTime object

    params = {
        "image_collection_id": "LANDSAT/LC09/C02/T1_L2",
        "filters": "CLOUD_COVER:<:10;SUN_ELEVATION:>:0",
        "start_date": start_date,
        "end_date": end_date,
        "extent": None,
        "extent_crs": None,
        "compositing_method": 0,  # Mosaic index
        "percentile_value": None,
        "viz_params": {},
    }

    # Run the algorithm with parameters
    run_algorithm_with_params(params)

    # Validate that the layer was added to the map
    layer = clean_qgis_iface.mapCanvas().layers()[0]
    assert layer.name() == "IC: LANDSAT/LC09/C02/T1_L2 (Mosaic)"
    assert layer.dataProvider().name() == "EE"


def test_add_image_collection_algorithm_multiple_filters(clean_qgis_iface):
    start_date = QDateTime(2021, 1, 1, 12, 0, 0)
    end_date = QDateTime(2021, 12, 31, 12, 0, 0)

    params = {
        "image_collection_id": "LANDSAT/LC09/C02/T1_L2",
        "filters": "CLOUD_COVER:<:10;SUN_ELEVATION:>:0",
        "start_date": start_date,
        "end_date": end_date,
        "extent": None,
        "extent_crs": None,
        "compositing_method": 0,  # Mosaic index
        "percentile_value": None,
        "viz_params": {},
    }

    # Run the algorithm with parameters
    run_algorithm_with_params(params)

    # Validate that the layer was added to the map
    layer = clean_qgis_iface.mapCanvas().layers()[0]
    assert layer.name() == "IC: LANDSAT/LC09/C02/T1_L2 (Mosaic)"
    assert layer.dataProvider().name() == "EE"


def test_invalid_filters(clean_qgis_iface):
    start_date = QDateTime(2021, 1, 1, 12, 0, 0)
    end_date = QDateTime(2021, 12, 31, 12, 0, 0)

    params = {
        "image_collection_id": "LANDSAT/LC09/C02/T1_L2",
        "filters": "INVALID_FILTER",
        "start_date": start_date,
        "end_date": end_date,
        "extent": None,
        "extent_crs": None,
        "compositing_method": "Mosaic",
        "percentile_value": None,
        "viz_params": {},
    }

    # Run the algorithm with invalid filters
    try:
        run_algorithm_with_params(params)
    except Exception:
        pass

    # Verify no layer is added to the map
    assert len(clean_qgis_iface.mapCanvas().layers()) == 0


def test_add_image_collection_algorithm_empty_filters(clean_qgis_iface):
    start_date = QDateTime(2021, 1, 1, 12, 0, 0)
    end_date = QDateTime(2021, 12, 31, 12, 0, 0)

    params = {
        "image_collection_id": "LANDSAT/LC09/C02/T1_L2",
        "filters": None,
        "start_date": start_date,
        "end_date": end_date,
        "extent": None,
        "extent_crs": None,
        "compositing_method": 0,  # Mosaic index
        "percentile_value": None,
        "viz_params": "{}",
    }

    # Run the algorithm with empty filters
    run_algorithm_with_params(params)

    # Validate that the layer was added to the map
    layer = clean_qgis_iface.mapCanvas().layers()[0]
    assert layer.name() == "IC: LANDSAT/LC09/C02/T1_L2 (Mosaic)"
    assert layer.dataProvider().name() == "EE"


def test_add_image_collection_algorithm_percentile_compositing(clean_qgis_iface):
    start_date = QDateTime(2021, 1, 1, 12, 0, 0)
    end_date = QDateTime(2021, 12, 31, 12, 0, 0)

    params = {
        "image_collection_id": "LANDSAT/LC09/C02/T1_L2",
        "filters": "CLOUD_COVER:<:10",
        "start_date": start_date,
        "end_date": end_date,
        "extent": None,
        "extent_crs": None,
        "compositing_method": 5,  # Percentile index
        "percentile_value": 90,
        "viz_params": {},
    }

    # Run the algorithm with percentile compositing method
    run_algorithm_with_params(params)

    # Validate that the layer was added to the map with the correct compositing method
    layer = clean_qgis_iface.mapCanvas().layers()[0]
    assert layer.name() == "IC: LANDSAT/LC09/C02/T1_L2 (Percentile 90%)"
    assert layer.dataProvider().name() == "EE"


def test_add_image_collection_algorithm_invalid_json_viz_params(clean_qgis_iface):
    start_date = QDateTime(2021, 1, 1, 12, 0, 0)
    end_date = QDateTime(2021, 12, 31, 12, 0, 0)

    params = {
        "image_collection_id": "LANDSAT/LC09/C02/T1_L2",
        "filters": "CLOUD_COVER:<:10",
        "start_date": start_date,
        "end_date": end_date,
        "extent": None,
        "extent_crs": None,
        "compositing_method": "Mosaic",
        "percentile_value": None,
        "viz_params": "not a valid JSON string",
    }

    try:
        run_algorithm_with_params(params)
    except Exception:
        pass

    # Verify no layer is added to the map
    assert len(clean_qgis_iface.mapCanvas().layers()) == 0


def test_empty_viz_params(clean_qgis_iface):
    start_date = QDateTime(2021, 1, 1, 12, 0, 0)
    end_date = QDateTime(2021, 12, 31, 12, 0, 0)

    params = {
        "image_collection_id": "LANDSAT/LC09/C02/T1_L2",
        "filters": "CLOUD_COVER:<:10",
        "start_date": start_date,
        "end_date": end_date,
        "extent": None,
        "extent_crs": None,
        "compositing_method": 0,  # Mosaic index
        "percentile_value": None,
        "viz_params": "{}",
    }

    run_algorithm_with_params(params)

    # Validate that the layer was added to the map
    layer = clean_qgis_iface.mapCanvas().layers()[0]
    assert layer.name() == "IC: LANDSAT/LC09/C02/T1_L2 (Mosaic)"
    assert layer.dataProvider().name() == "EE"


# Parametrized test for different extent CRS cases
@pytest.mark.parametrize(
    "extent, extent_crs",
    [
        (
            QgsRectangle(-123.5, 49.5, -123.0, 50.0),
            QgsCoordinateReferenceSystem("EPSG:4326"),
        ),
        (
            QgsRectangle(-13700000, 6300000, -13680000, 6320000),
            QgsCoordinateReferenceSystem("EPSG:3857"),
        ),
    ],
)
def test_add_image_collection_with_varied_extent_crs(
    clean_qgis_iface, extent, extent_crs
):
    start_date = QDateTime(2021, 1, 1, 12, 0, 0)
    end_date = QDateTime(2021, 12, 31, 12, 0, 0)

    params = {
        "image_collection_id": "LANDSAT/LC09/C02/T1_L2",
        "filters": "CLOUD_COVER:<:10",
        "start_date": start_date,
        "end_date": end_date,
        "extent": extent,
        "extent_crs": extent_crs,
        "compositing_method": 0,
        "percentile_value": None,
        "viz_params": "{}",
    }

    run_algorithm_with_params(params)
    layer = clean_qgis_iface.mapCanvas().layers()[0]
    assert layer.name().startswith("IC:")
    assert layer.dataProvider().name() == "EE"
