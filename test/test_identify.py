from unittest.mock import Mock, patch

from qgis.core import NULL, QgsProject, QgsPointXY, QgsRectangle

from ee_plugin.identify import (
    _geojson_geometry_to_wkt,
    add_identify_results_layer,
    identify_features,
    identify_image,
    identify_reducer,
    identify_reducer_name,
    identify_result_field_name,
    point_to_ee_geometry,
    rectangle_to_ee_geometry,
)


def test_identify_image_reduces_all_bands_over_geometry():
    image = Mock()
    image.reduceRegion.return_value.getInfo.return_value = {
        "B2": 0.12,
        "B3": 0.34,
    }
    geometry = Mock()
    reducer = Mock()

    values = identify_image(image, geometry, 30, reducer)

    image.reduceRegion.assert_called_once_with(
        reducer=reducer,
        geometry=geometry,
        scale=30,
        bestEffort=True,
        maxPixels=100_000_000,
    )
    assert values == {"B2": 0.12, "B3": 0.34}


def test_identify_features_fetches_intersecting_features():
    feature_collection = Mock()
    filtered = feature_collection.filterBounds.return_value
    limited = filtered.limit.return_value
    limited.getInfo.return_value = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "feature-1",
                "geometry": {"type": "Point", "coordinates": [-123.1, 49.2]},
                "properties": {"name": "Selected"},
            }
        ],
    }
    geometry = Mock()

    features = identify_features(feature_collection, geometry, limit=10)

    feature_collection.filterBounds.assert_called_once_with(geometry)
    filtered.limit.assert_called_once_with(10)
    assert features == limited.getInfo.return_value["features"]


def test_geojson_geometry_to_wkt_handles_polygon():
    wkt = _geojson_geometry_to_wkt(
        {
            "type": "Polygon",
            "coordinates": [
                [
                    [-123.2, 49.1],
                    [-123.1, 49.1],
                    [-123.1, 49.2],
                    [-123.2, 49.1],
                ]
            ],
        }
    )

    assert wkt == "POLYGON ((-123.2 49.1, -123.1 49.1, -123.1 49.2, -123.2 49.1))"


def test_point_to_ee_geometry():
    with patch("ee_plugin.identify.ee.Geometry.Point") as point_geometry:
        result = point_to_ee_geometry(QgsPointXY(-123.1, 49.2))

    point_geometry.assert_called_once_with([-123.1, 49.2], "EPSG:4326")
    assert result is point_geometry.return_value


def test_rectangle_to_ee_geometry():
    qgis_geometry = Mock()
    qgis_geometry.asPolygon.return_value = [
        [
            QgsPointXY(-123.2, 49.1),
            QgsPointXY(-123.1, 49.1),
            QgsPointXY(-123.1, 49.2),
            QgsPointXY(-123.2, 49.1),
        ]
    ]
    transform = Mock()

    with (
        patch(
            "ee_plugin.identify.QgsGeometry.fromRect",
            return_value=qgis_geometry,
        ) as from_rect,
        patch("ee_plugin.identify.ee.Geometry.Polygon") as polygon,
    ):
        rectangle = QgsRectangle(-123.2, 49.1, -123.1, 49.2)
        result = rectangle_to_ee_geometry(rectangle, transform)

    from_rect.assert_called_once_with(rectangle)
    qgis_geometry.transform.assert_called_once_with(transform)
    polygon.assert_called_once_with(
        [
            [
                [-123.2, 49.1],
                [-123.1, 49.1],
                [-123.1, 49.2],
                [-123.2, 49.1],
            ]
        ],
        "EPSG:4326",
        False,
    )
    assert result is polygon.return_value


def test_identify_reducer_matches_selection_type():
    with (
        patch("ee_plugin.identify.ee.Reducer.first") as first,
        patch("ee_plugin.identify.ee.Reducer.mean") as mean,
    ):
        point_reducer = identify_reducer(False)
        region_reducer = identify_reducer(True)

    first.assert_called_once_with()
    mean.assert_called_once_with()
    assert point_reducer is first.return_value
    assert region_reducer is mean.return_value


def test_identify_reducer_name_matches_selection_type():
    assert identify_reducer_name(False) == "first"
    assert identify_reducer_name(True) == "mean"


def test_identify_result_field_name_includes_reducer_and_is_qgis_safe():
    assert identify_result_field_name("B2", "mean") == "B2_mean"
    assert identify_result_field_name("SR B5/QA", "first") == "SR_B5_QA_first"
    assert identify_result_field_name("2024-band", "mean") == "band_2024_band_mean"


def test_add_identify_results_layer_creates_single_region_feature():
    result = {
        "layer": "DEM",
        "selection_type": "region",
        "reducer": "mean",
        "scale": 30,
        "geometry": {
            "west": -123.2,
            "south": 49.1,
            "east": -123.1,
            "north": 49.2,
        },
        "values": {"B2": 0.12, "B3": None},
    }

    layer = add_identify_results_layer(result, QgsProject.instance())

    assert layer.name() == "DEM identify"
    assert layer.geometryType() == 2
    assert [field.name() for field in layer.fields()] == [
        "source_layer",
        "selection_type",
        "statistic",
        "scale_m",
        "west",
        "south",
        "east",
        "north",
        "B2_mean",
        "B3_mean",
    ]
    features = list(layer.getFeatures())
    assert len(features) == 1
    feature = features[0]
    assert feature["source_layer"] == "DEM"
    assert feature["selection_type"] == "region"
    assert feature["statistic"] == "mean"
    assert feature["B2_mean"] == 0.12
    assert feature["B3_mean"] in (None, NULL)
    assert feature.geometry().boundingBox() == QgsRectangle(-123.2, 49.1, -123.1, 49.2)


def test_add_identify_results_layer_creates_single_point_feature():
    result = {
        "layer": "DEM",
        "selection_type": "point",
        "reducer": "first",
        "scale": 30,
        "geometry": {"longitude": -123.1, "latitude": 49.2},
        "values": {"elevation": 123},
    }

    layer = add_identify_results_layer(result, QgsProject.instance())
    feature = next(layer.getFeatures())

    assert [field.name() for field in layer.fields()] == [
        "source_layer",
        "selection_type",
        "statistic",
        "scale_m",
        "longitude",
        "latitude",
        "elevation_first",
    ]
    assert feature["elevation_first"] == 123
    assert feature.geometry().asPoint() == QgsPointXY(-123.1, 49.2)


def test_add_identify_results_layer_creates_selected_feature_layer():
    result = {
        "result_type": "features",
        "layer": "FC: Counties",
        "selection_type": "point",
        "geometry": {"longitude": -123.1, "latitude": 49.2},
        "features": [
            {
                "type": "Feature",
                "id": "county-1",
                "geometry": {"type": "Point", "coordinates": [-123.1, 49.2]},
                "properties": {
                    "name": "Selected County",
                    "population": 123,
                    "2020/id": "abc",
                },
            }
        ],
    }

    layer = add_identify_results_layer(result, QgsProject.instance())
    feature = next(layer.getFeatures())

    assert layer.name() == "FC: Counties identify"
    assert [field.name() for field in layer.fields()] == [
        "source_layer",
        "selection_type",
        "ee_feature_id",
        "name",
        "population",
        "property_2020_id",
    ]
    assert feature["source_layer"] == "FC: Counties"
    assert feature["selection_type"] == "point"
    assert feature["ee_feature_id"] == "county-1"
    assert feature["name"] == "Selected County"
    assert feature["population"] == 123
    assert feature["property_2020_id"] == "abc"
    assert feature.geometry().asPoint() == QgsPointXY(-123.1, 49.2)


def test_add_identify_results_layer_disambiguates_sanitized_band_fields():
    result = {
        "layer": "DEM",
        "selection_type": "point",
        "reducer": "first",
        "scale": 30,
        "geometry": {"longitude": -123.1, "latitude": 49.2},
        "values": {"SR B5": 1, "SR-B5": 2},
    }

    layer = add_identify_results_layer(result, QgsProject.instance())
    feature = next(layer.getFeatures())
    field_names = [field.name() for field in layer.fields()]

    assert "SR_B5_first" in field_names
    assert "SR_B5_first_2" in field_names
    assert feature["SR_B5_first"] == 1
    assert feature["SR_B5_first_2"] == 2


def test_add_identify_results_layer_creates_multi_layer_features():
    result = {
        "selection_type": "point",
        "reducer": "first",
        "scale": 30,
        "geometry": {"longitude": -123.1, "latitude": 49.2},
        "results": [
            {
                "layer": "DEM",
                "selection_type": "point",
                "reducer": "first",
                "scale": 30,
                "geometry": {"longitude": -123.1, "latitude": 49.2},
                "values": {"elevation": 123},
            },
            {
                "layer": "NDVI",
                "selection_type": "point",
                "reducer": "first",
                "scale": 30,
                "geometry": {"longitude": -123.1, "latitude": 49.2},
                "values": {"ndvi": 0.42},
            },
        ],
    }

    layer = add_identify_results_layer(result, QgsProject.instance())

    assert layer.name() == "Earth Engine identify"
    assert [field.name() for field in layer.fields()] == [
        "source_layer",
        "selection_type",
        "statistic",
        "scale_m",
        "longitude",
        "latitude",
        "band",
        "value",
    ]
    features = list(layer.getFeatures())
    assert len(features) == 2
    assert features[0]["source_layer"] == "DEM"
    assert features[0]["band"] == "elevation"
    assert features[0]["value"] == "123"
    assert features[1]["source_layer"] == "NDVI"
    assert features[1]["band"] == "ndvi"
    assert features[1]["value"] == "0.42"
