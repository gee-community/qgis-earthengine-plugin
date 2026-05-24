import ee
import pytest
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsMapLayer, QgsProject, QgsWkbTypes

from ee_plugin import Map

# initialize the Earth Engine API is required to use the ee.Geometry module
#   and runs before fixtures
ee.Initialize()


def qgis_geometry_type(name):
    geometry_enum = getattr(QgsWkbTypes, "GeometryType", QgsWkbTypes)
    return getattr(geometry_enum, name)


def expected_qcolor(value):
    color_value = value.strip()
    if not color_value.startswith("#") and len(color_value) in (3, 6, 8):
        try:
            int(color_value, 16)
            color_value = f"#{color_value}"
        except ValueError:
            pass
    return QColor(color_value)


geometries = [
    (ee.Geometry.Point([1.5, 1.5]), {"color": "1eff05"}, "point"),
    (
        ee.Geometry.LineString([[-35, -10], [35, -10], [35, 10], [-35, 10]]),
        {"color": "FF0000"},
        "lineString",
    ),
    (
        ee.Geometry.LinearRing(
            [[-35, -10], [35, -10], [35, 10], [-35, 10], [-35, -10]]
        ),
        {"color": "ee38ff"},
        "linearRing",
    ),
    (ee.Geometry.Rectangle([-40, -20, 40, 20]), {"color": "ffa05c"}, "rectangle"),
    (
        ee.Geometry.Polygon([[[-5, 40], [65, 40], [65, 60], [-5, 60], [-5, 40]]]),
        {"color": "FF0000"},
        "geodesic polygon",
    ),
    (
        ee.Geometry(
            ee.Geometry.Polygon([[[-5, 40], [65, 40], [65, 60], [-5, 60], [-5, 40]]]),
            None,
            False,
        ),
        {"color": "000000"},
        "planar polygon",
    ),
]


@pytest.mark.parametrize("geometry, vis_params, layer_name", geometries)
def test_add_geometry_layer(geometry, vis_params, layer_name):
    qgis_instance = QgsProject.instance()
    Map.addLayer(geometry, vis_params, layer_name)

    layers = qgis_instance.mapLayersByName(layerName=layer_name)
    assert len(layers) == 1, "Wrong number of layers added"

    layer = layers[0]
    assert layer, "Layer not found"
    assert layer.name() == layer_name, "Layer name mismatch"
    assert layer.type() == QgsMapLayer.LayerType.VectorLayer, (
        "Layer is not a vector layer"
    )

    if "color" in vis_params:
        renderer = layer.renderer()
        if not renderer or not renderer.symbol():
            pytest.skip("QGIS/OGR loaded this geometry without a renderable symbol")
        symbol = renderer.symbol()
        symbol_layer = symbol.symbolLayer(0)
        expected_color = expected_qcolor(vis_params["color"])
        geometry_type = layer.geometryType()

        if geometry_type == qgis_geometry_type("PointGeometry"):
            assert symbol_layer.color() == expected_color, (
                f"Expected point fill {expected_color.name()}, "
                f"got {symbol_layer.color().name()}"
            )
            assert symbol_layer.strokeColor() == expected_color, (
                f"Expected point stroke {expected_color.name()}, "
                f"got {symbol_layer.strokeColor().name()}"
            )
        elif geometry_type == qgis_geometry_type("LineGeometry"):
            assert symbol_layer.color() == expected_color, (
                f"Expected line color {expected_color.name()}, "
                f"got {symbol_layer.color().name()}"
            )
        elif geometry_type == qgis_geometry_type("PolygonGeometry"):
            assert symbol_layer.strokeColor() == expected_color, (
                f"Expected polygon stroke {expected_color.name()}, "
                f"got {symbol_layer.strokeColor().name()}"
            )
            assert symbol_layer.fillColor() == expected_color, (
                f"Expected polygon fill {expected_color.name()}, "
                f"got {symbol_layer.fillColor().name()}"
            )


def test_geometry_fill_color_override():
    qgis_instance = QgsProject.instance()
    polygon = ee.Geometry.Polygon([[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]])
    Map.addLayer(polygon, {"color": "red", "fillColor": "blue"}, "fill_override")

    layers = qgis_instance.mapLayersByName("fill_override")
    assert len(layers) == 1
    layer = layers[0]
    symbol_layer = layer.renderer().symbol().symbolLayer(0)

    assert symbol_layer.strokeColor() == expected_qcolor("red")
    assert symbol_layer.fillColor() == expected_qcolor("blue")


def test_line_geometry_specific_override():
    qgis_instance = QgsProject.instance()
    line = ee.Geometry.LineString([[0, 0], [10, 10]])
    Map.addLayer(line, {"color": "red", "lineColor": "green"}, "line_override")

    layers = qgis_instance.mapLayersByName("line_override")
    assert len(layers) == 1
    layer = layers[0]
    symbol_layer = layer.renderer().symbol().symbolLayer(0)

    assert symbol_layer.color() == expected_qcolor("green")


def test_geometry_width_property():
    qgis_instance = QgsProject.instance()
    polygon = ee.Geometry.Rectangle([0, 0, 10, 10])
    Map.addLayer(polygon, {"color": "black", "width": 5}, "width_test")

    layers = qgis_instance.mapLayersByName("width_test")
    assert len(layers) == 1
    layer = layers[0]
    symbol_layer = layer.renderer().symbol().symbolLayer(0)

    assert symbol_layer.strokeWidth() == 5


def test_filtered_feature_collection_with_color():
    qgis_instance = QgsProject.instance()
    countries = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
    ukraine = countries.filter(ee.Filter.eq("country_na", "Ukraine"))

    Map.addLayer(ukraine, {"color": "orange"}, "ukraine_test")

    layers = qgis_instance.mapLayersByName("ukraine_test")
    assert len(layers) == 1, "Wrong number of layers added"
    layer = layers[0]
    assert layer.name() == "ukraine_test", "Layer name mismatch"


def test_line_type_mapping():
    """Verify GEE lineType values map correctly to QGIS pen styles."""
    from qgis.PyQt.QtCore import Qt

    qgis_instance = QgsProject.instance()
    line = ee.Geometry.LineString([[0, 0], [10, 10]])

    # Test "dashed" (official GEE value)
    Map.addLayer(line, {"lineColor": "blue", "lineType": "dashed"}, "line_dashed")
    layer = qgis_instance.mapLayersByName("line_dashed")[0]
    symbol_layer = layer.renderer().symbol().symbolLayer(0)
    assert symbol_layer.penStyle() == Qt.PenStyle.DashLine

    # Test "dotted" (official GEE value)
    Map.addLayer(line, {"lineColor": "blue", "lineType": "dotted"}, "line_dotted")
    layer = qgis_instance.mapLayersByName("line_dotted")[0]
    symbol_layer = layer.renderer().symbol().symbolLayer(0)
    assert symbol_layer.penStyle() == Qt.PenStyle.DotLine


def test_polygon_stroke_type_mapping():
    """Verify GEE polygonStrokeType values map correctly to QGIS stroke styles."""
    from qgis.PyQt.QtCore import Qt

    qgis_instance = QgsProject.instance()
    polygon = ee.Geometry.Polygon([[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]])

    # Test "dashed" for polygon stroke
    Map.addLayer(
        polygon,
        {"polygonStrokeColor": "red", "polygonStrokeType": "dashed"},
        "polygon_dashed",
    )
    layer = qgis_instance.mapLayersByName("polygon_dashed")[0]
    symbol_layer = layer.renderer().symbol().symbolLayer(0)
    assert symbol_layer.strokeStyle() == Qt.PenStyle.DashLine

    # Test "dotted" for polygon stroke
    Map.addLayer(
        polygon,
        {"polygonStrokeColor": "red", "polygonStrokeType": "dotted"},
        "polygon_dotted",
    )
    layer = qgis_instance.mapLayersByName("polygon_dotted")[0]
    symbol_layer = layer.renderer().symbol().symbolLayer(0)
    assert symbol_layer.strokeStyle() == Qt.PenStyle.DotLine


def test_vector_update_normalizes_geometry_types():
    """Raw EE Geometry objects must be normalized to FeatureCollection on update."""
    qgis_instance = QgsProject.instance()
    point = ee.Geometry.Point([1.5, 1.5])

    # First add
    Map.addLayer(point, {"color": "red"}, "geom_normalize_test")
    layers = qgis_instance.mapLayersByName("geom_normalize_test")
    assert len(layers) == 1
    assert layers[0].isValid(), "Initial Point layer must be valid"

    # Update
    Map.addLayer(point, {"color": "blue"}, "geom_normalize_test")
    layers = qgis_instance.mapLayersByName("geom_normalize_test")
    assert len(layers) == 1, "Update must not duplicate"
    assert layers[0].isValid(), "Updated Point layer must be valid"
    assert layers[0].customProperty("ee-layer") is True
    source = layers[0].source()
    assert source.endswith(".geojson") or source.endswith(".geojson.gz")


def test_data_catalog_vector_layer():
    qgis_instance = QgsProject.instance()

    ecoregions = ee.FeatureCollection("RESOLVE/ECOREGIONS/2017")

    Map.addLayer(ecoregions, {}, "ecoregions")

    layers = qgis_instance.mapLayersByName(layerName="ecoregions")
    assert len(layers) == 1, "Wrong number of layers added"
    assert layers[0].name() == "ecoregions", "Layer name mismatch"
    assert layers[0].type() == QgsMapLayer.LayerType.RasterLayer, (
        "Layer is treated as raster layer"
    )
