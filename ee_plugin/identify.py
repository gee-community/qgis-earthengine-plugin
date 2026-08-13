"""Map tool for identifying Earth Engine raster pixels and vector features."""

import re
from typing import Any, Dict, List, Optional

import ee
from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsRectangle,
    QgsVectorLayer,
)
from qgis.gui import QgsMapTool, QgsMapMouseEvent, QgsRubberBand, QgsVertexMarker
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from . import Map, utils

FEATURE_IDENTIFY_LIMIT = 100


def identify_image(
    image: ee.Image, geometry: ee.Geometry, scale: float, reducer: ee.Reducer
) -> Dict[str, Any]:
    """Reduce every image band over an Earth Engine geometry."""
    return image.reduceRegion(
        reducer=reducer,
        geometry=geometry,
        scale=scale,
        bestEffort=True,
        maxPixels=100_000_000,
    ).getInfo()


def identify_features(
    feature_collection: ee.FeatureCollection,
    geometry: ee.Geometry,
    limit: int = FEATURE_IDENTIFY_LIMIT,
) -> List[Dict[str, Any]]:
    """Fetch features from a collection that intersect an Earth Engine geometry."""
    info = feature_collection.filterBounds(geometry).limit(limit).getInfo()
    return info.get("features", [])


def point_to_ee_geometry(point: QgsPointXY) -> ee.Geometry:
    """Create a WGS84 Earth Engine point from a QGIS point."""
    return ee.Geometry.Point([point.x(), point.y()], "EPSG:4326")


def rectangle_to_ee_geometry(
    rectangle: QgsRectangle, transform: QgsCoordinateTransform
) -> ee.Geometry:
    """Create a WGS84 Earth Engine polygon from a map rectangle."""
    coordinates = rectangle_to_wgs84_coordinates(rectangle, transform)
    return ee.Geometry.Polygon([coordinates], "EPSG:4326", False)


def rectangle_to_wgs84_coordinates(
    rectangle: QgsRectangle, transform: QgsCoordinateTransform
) -> list[list[float]]:
    """Transform a map rectangle to a WGS84 polygon coordinate ring."""
    geometry = QgsGeometry.fromRect(rectangle)
    geometry.transform(transform)
    polygon = geometry.asPolygon()[0]
    return [[point.x(), point.y()] for point in polygon]


def identify_reducer(is_region: bool) -> ee.Reducer:
    """Use a representative pixel for clicks and means for dragged regions."""
    return ee.Reducer.mean() if is_region else ee.Reducer.first()


def identify_reducer_name(is_region: bool) -> str:
    """Return the field suffix for the reducer used by the selection."""
    return "mean" if is_region else "first"


def identify_result_field_name(band: str, reducer_name: str) -> str:
    """Create a stable QGIS attribute name for a band statistic."""
    base = re.sub(r"[^0-9A-Za-z_]+", "_", str(band)).strip("_") or "band"
    if base[0].isdigit():
        base = f"band_{base}"
    return f"{base}_{reducer_name}"


def add_identify_results_layer(
    result: Dict[str, Any], project: Optional[QgsProject] = None
) -> QgsVectorLayer:
    """Add identify results as a temporary single-feature layer."""
    if result.get("result_type") == "features":
        return _add_feature_identify_results_layer(result, project)
    if "results" in result:
        return _add_multi_identify_results_layer(result, project)

    layer = _new_result_layer(result)
    fields = _result_fields(result)
    provider = layer.dataProvider()
    provider.addAttributes(fields)
    layer.updateFields()

    feature = QgsFeature(layer.fields())
    feature.setGeometry(_result_geometry(result))
    attributes = _result_attributes(result)
    feature.setAttributes([attributes.get(field.name()) for field in layer.fields()])

    if not provider.addFeatures([feature]):
        raise ValueError("Could not add identify feature to the temporary layer.")
    layer.updateExtents()

    (project or QgsProject.instance()).addMapLayer(layer)
    return layer


def _add_feature_identify_results_layer(
    result: Dict[str, Any], project: Optional[QgsProject] = None
) -> QgsVectorLayer:
    """Add selected EE features as a temporary vector layer."""
    layer = _new_feature_result_layer(result)
    fields = _feature_result_fields(result)
    provider = layer.dataProvider()
    provider.addAttributes(fields)
    layer.updateFields()

    features = []
    for feature_info in result["features"]:
        feature = QgsFeature(layer.fields())
        geometry_info = feature_info.get("geometry")
        if geometry_info:
            feature.setGeometry(_geojson_to_qgs_geometry(geometry_info))
        attributes = _feature_result_attributes(result, feature_info)
        feature.setAttributes(
            [attributes.get(field.name()) for field in layer.fields()]
        )
        features.append(feature)

    if features and not provider.addFeatures(features):
        raise ValueError("Could not add identify features to the temporary layer.")
    layer.updateExtents()

    (project or QgsProject.instance()).addMapLayer(layer)
    return layer


def _add_multi_identify_results_layer(
    result: Dict[str, Any], project: Optional[QgsProject] = None
) -> QgsVectorLayer:
    """Add multi-layer identify results as one feature per layer/band value."""
    layer = _new_multi_result_layer(result)
    fields = _multi_result_fields(result)
    provider = layer.dataProvider()
    provider.addAttributes(fields)
    layer.updateFields()

    features = []
    for layer_result in result["results"]:
        feature_geometry = _result_geometry(layer_result)
        for band, value in layer_result["values"].items():
            feature = QgsFeature(layer.fields())
            feature.setGeometry(feature_geometry)
            attributes = _multi_result_attributes(layer_result, band, value)
            feature.setAttributes(
                [attributes.get(field.name()) for field in layer.fields()]
            )
            features.append(feature)

        if not layer_result["values"]:
            feature = QgsFeature(layer.fields())
            feature.setGeometry(feature_geometry)
            attributes = _multi_result_attributes(layer_result, None, None)
            feature.setAttributes(
                [attributes.get(field.name()) for field in layer.fields()]
            )
            features.append(feature)

    if features and not provider.addFeatures(features):
        raise ValueError("Could not add identify features to the temporary layer.")
    layer.updateExtents()

    (project or QgsProject.instance()).addMapLayer(layer)
    return layer


def _new_result_layer(result: Dict[str, Any]) -> QgsVectorLayer:
    geometry_type = "Polygon" if result["selection_type"] == "region" else "Point"
    layer = QgsVectorLayer(
        f"{geometry_type}?crs=EPSG:4326",
        f"{result['layer']} identify",
        "memory",
    )
    if not layer.isValid():
        raise ValueError("Could not create a temporary identify layer.")
    return layer


def _new_multi_result_layer(result: Dict[str, Any]) -> QgsVectorLayer:
    geometry_type = "Polygon" if result["selection_type"] == "region" else "Point"
    layer = QgsVectorLayer(
        f"{geometry_type}?crs=EPSG:4326",
        "Earth Engine identify",
        "memory",
    )
    if not layer.isValid():
        raise ValueError("Could not create a temporary identify layer.")
    return layer


def _new_feature_result_layer(result: Dict[str, Any]) -> QgsVectorLayer:
    geometry_type = _feature_result_geometry_type(result)
    layer = QgsVectorLayer(
        f"{geometry_type}?crs=EPSG:4326",
        f"{result['layer']} identify",
        "memory",
    )
    if not layer.isValid():
        raise ValueError("Could not create a temporary feature identify layer.")
    return layer


def _feature_result_geometry_type(result: Dict[str, Any]) -> str:
    for feature_info in result["features"]:
        geometry_info = feature_info.get("geometry") or {}
        geometry_type = geometry_info.get("type")
        if geometry_type in (
            "Point",
            "MultiPoint",
            "LineString",
            "MultiLineString",
            "Polygon",
            "MultiPolygon",
        ):
            return geometry_type
    return "Point"


def _result_fields(result: Dict[str, Any]) -> QgsFields:
    fields = QgsFields()
    for name, field_type in [
        ("source_layer", QVariant.String),
        ("selection_type", QVariant.String),
        ("statistic", QVariant.String),
        ("scale_m", QVariant.Double),
    ]:
        fields.append(QgsField(name, field_type))

    if result["selection_type"] == "point":
        fields.append(QgsField("longitude", QVariant.Double))
        fields.append(QgsField("latitude", QVariant.Double))
    else:
        for name in ["west", "south", "east", "north"]:
            fields.append(QgsField(name, QVariant.Double))

    band_fields = _band_field_names(result)
    for band, value in result["values"].items():
        fields.append(
            QgsField(
                band_fields[band],
                _qvariant_type(value),
            )
        )
    return fields


def _feature_result_fields(result: Dict[str, Any]) -> QgsFields:
    fields = QgsFields()
    for name, field_type in [
        ("source_layer", QVariant.String),
        ("selection_type", QVariant.String),
        ("ee_feature_id", QVariant.String),
    ]:
        fields.append(QgsField(name, field_type))

    field_names = _feature_property_field_names(result)
    sample_values = {}
    for feature_info in result["features"]:
        sample_values.update(feature_info.get("properties", {}))

    for property_name, field_name in field_names.items():
        fields.append(
            QgsField(
                field_name,
                _qvariant_type(sample_values.get(property_name)),
            )
        )
    return fields


def _multi_result_fields(result: Dict[str, Any]) -> QgsFields:
    fields = QgsFields()
    for name, field_type in [
        ("source_layer", QVariant.String),
        ("selection_type", QVariant.String),
        ("statistic", QVariant.String),
        ("scale_m", QVariant.Double),
    ]:
        fields.append(QgsField(name, field_type))

    if result["selection_type"] == "point":
        fields.append(QgsField("longitude", QVariant.Double))
        fields.append(QgsField("latitude", QVariant.Double))
    else:
        for name in ["west", "south", "east", "north"]:
            fields.append(QgsField(name, QVariant.Double))

    fields.append(QgsField("band", QVariant.String))
    fields.append(QgsField("value", QVariant.String))
    return fields


def _geojson_to_qgs_geometry(geometry_info: Dict[str, Any]) -> QgsGeometry:
    return QgsGeometry.fromWkt(_geojson_geometry_to_wkt(geometry_info))


def _geojson_geometry_to_wkt(geometry_info: Dict[str, Any]) -> str:
    geometry_type = geometry_info.get("type")
    coordinates = geometry_info.get("coordinates")
    if geometry_type == "Point":
        return f"POINT ({_wkt_coordinate(coordinates)})"
    if geometry_type == "MultiPoint":
        return "MULTIPOINT ({})".format(
            ", ".join(f"({_wkt_coordinate(point)})" for point in coordinates)
        )
    if geometry_type == "LineString":
        return f"LINESTRING ({_wkt_coordinate_sequence(coordinates)})"
    if geometry_type == "MultiLineString":
        return "MULTILINESTRING ({})".format(
            ", ".join(f"({_wkt_coordinate_sequence(line)})" for line in coordinates)
        )
    if geometry_type == "Polygon":
        return f"POLYGON ({_wkt_polygon_coordinates(coordinates)})"
    if geometry_type == "MultiPolygon":
        return "MULTIPOLYGON ({})".format(
            ", ".join(
                f"({_wkt_polygon_coordinates(polygon)})" for polygon in coordinates
            )
        )
    raise ValueError(f"Unsupported feature geometry type: {geometry_type}")


def _wkt_polygon_coordinates(rings: List[Any]) -> str:
    return ", ".join(f"({_wkt_coordinate_sequence(ring)})" for ring in rings)


def _wkt_coordinate_sequence(coordinates: List[Any]) -> str:
    return ", ".join(_wkt_coordinate(coordinate) for coordinate in coordinates)


def _wkt_coordinate(coordinate: List[Any]) -> str:
    return f"{coordinate[0]} {coordinate[1]}"


def _result_geometry(result: Dict[str, Any]) -> QgsGeometry:
    if "feature_geometry" in result:
        return QgsGeometry(result["feature_geometry"])

    geometry = result["geometry"]
    if result["selection_type"] == "point":
        return QgsGeometry.fromPointXY(
            QgsPointXY(geometry["longitude"], geometry["latitude"])
        )

    return QgsGeometry.fromRect(
        QgsRectangle(
            geometry["west"],
            geometry["south"],
            geometry["east"],
            geometry["north"],
        )
    )


def _result_attributes(result: Dict[str, Any]) -> Dict[str, Any]:
    attributes = {
        "source_layer": result["layer"],
        "selection_type": result["selection_type"],
        "statistic": result["reducer"],
        "scale_m": result["scale"],
    }
    attributes.update(result["geometry"])
    band_fields = _band_field_names(result)
    for band, value in result["values"].items():
        attributes[band_fields[band]] = value
    return attributes


def _feature_result_attributes(
    result: Dict[str, Any], feature_info: Dict[str, Any]
) -> Dict[str, Any]:
    attributes = {
        "source_layer": feature_info.get("_source_layer", result["layer"]),
        "selection_type": result["selection_type"],
        "ee_feature_id": str(feature_info.get("id", "")),
    }
    field_names = _feature_property_field_names(result)
    for property_name, value in feature_info.get("properties", {}).items():
        attributes[field_names[property_name]] = _qgis_attribute_value(value)
    return attributes


def _multi_result_attributes(
    result: Dict[str, Any], band: Optional[str], value: Any
) -> Dict[str, Any]:
    attributes = {
        "source_layer": result["layer"],
        "selection_type": result["selection_type"],
        "statistic": result["reducer"],
        "scale_m": result["scale"],
        "band": band,
        "value": _format_identify_value(value),
    }
    attributes.update(result["geometry"])
    return attributes


def _feature_property_field_names(result: Dict[str, Any]) -> Dict[str, str]:
    used_names = {"source_layer", "selection_type", "ee_feature_id"}
    field_names = {}
    for feature_info in result["features"]:
        for property_name in feature_info.get("properties", {}):
            if property_name in field_names:
                continue
            field_name = re.sub(r"[^0-9A-Za-z_]+", "_", str(property_name)).strip("_")
            field_name = field_name or "property"
            if field_name[0].isdigit():
                field_name = f"property_{field_name}"
            unique_field_name = field_name
            suffix = 2
            while unique_field_name in used_names:
                unique_field_name = f"{field_name}_{suffix}"
                suffix += 1
            used_names.add(unique_field_name)
            field_names[property_name] = unique_field_name
    return field_names


def _band_field_names(result: Dict[str, Any]) -> Dict[str, str]:
    used_names = {
        "source_layer",
        "selection_type",
        "statistic",
        "scale_m",
        "longitude",
        "latitude",
        "west",
        "south",
        "east",
        "north",
    }
    field_names = {}
    for band in result["values"]:
        field_name = identify_result_field_name(band, result["reducer"])
        unique_field_name = field_name
        suffix = 2
        while unique_field_name in used_names:
            unique_field_name = f"{field_name}_{suffix}"
            suffix += 1
        used_names.add(unique_field_name)
        field_names[band] = unique_field_name
    return field_names


def _qvariant_type(value: Any):
    if isinstance(value, bool):
        return QVariant.Bool
    if isinstance(value, int):
        return QVariant.LongLong
    if isinstance(value, float) or value is None:
        return QVariant.Double
    return QVariant.String


def _qgis_attribute_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


def _format_identify_value(value: Any) -> str:
    if value is None:
        return "No data"
    if isinstance(value, float):
        return f"{value:.8g}"
    return str(value)


class IdentifyResultsDialog(QDialog):
    """Display and add Earth Engine identify results to the project."""

    def __init__(self, result: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.result = result
        self.results = result.get("results", [result])
        if self._is_multi_result():
            self.setWindowTitle("Earth Engine Identify")
        else:
            self.setWindowTitle(f"Earth Engine Identify - {result['layer']}")
        self.setMinimumSize(480, 360)

        layout = QVBoxLayout(self)

        heading = self._heading_text()
        title = QLabel(f"<h2 style='margin: 0'>{heading}</h2>")
        subtitle = QLabel(self._subtitle_text())
        subtitle.setStyleSheet("color: palette(mid); margin-bottom: 8px;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        details = QFormLayout()
        details.addRow("Layer", QLabel(self._layer_text()))
        if "scale" in result:
            details.addRow("Scale", QLabel(f"{result['scale']:.3f} m"))
        details.addRow("Selection", QLabel(self._geometry_text()))
        layout.addLayout(details)

        table = self._create_values_table()
        layout.addWidget(table)

        if self._is_feature_result() and not self.result["features"]:
            empty_label = QLabel("No features intersect this selection.")
            empty_label.setStyleSheet("color: palette(mid); font-style: italic;")
            layout.addWidget(empty_label)
        elif not self._is_feature_result() and not any(
            layer_result["values"] for layer_result in self.results
        ):
            empty_label = QLabel("No unmasked data was found in this selection.")
            empty_label.setStyleSheet("color: palette(mid); font-style: italic;")
            layout.addWidget(empty_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Close
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Add Layer")
        buttons.clicked.connect(self._button_clicked)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _is_multi_result(self) -> bool:
        return "results" in self.result

    def _is_feature_result(self) -> bool:
        return self.result.get("result_type") == "features"

    def _heading_text(self) -> str:
        if self._is_feature_result():
            return "Selected features"
        return (
            "Region statistics"
            if self.result["selection_type"] == "region"
            else "Pixel values"
        )

    def _subtitle_text(self) -> str:
        if self._is_feature_result():
            return (
                "Feature properties for Earth Engine features intersecting the "
                "selection."
            )
        return (
            "Mean value for each band in the selected area."
            if self.result["selection_type"] == "region"
            else "First unmasked value for each band at the selected point."
        )

    def _layer_text(self) -> str:
        if not self._is_multi_result():
            return self.result["layer"]
        count = len(self.results)
        return f"{count} Earth Engine layers"

    def _create_values_table(self) -> QTableWidget:
        if self._is_feature_result():
            rows = sum(
                max(1, len(feature_info.get("properties", {})))
                for feature_info in self.result["features"]
            )
            table = QTableWidget(rows, 3)
            table.setHorizontalHeaderLabels(["Feature", "Property", "Value"])
            self._populate_feature_table(table)
            table.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.ResizeMode.ResizeToContents
            )
            table.horizontalHeader().setSectionResizeMode(
                1, QHeaderView.ResizeMode.Stretch
            )
            table.horizontalHeader().setSectionResizeMode(
                2, QHeaderView.ResizeMode.Stretch
            )
        elif self._is_multi_result():
            rows = sum(
                max(1, len(layer_result["values"])) for layer_result in self.results
            )
            table = QTableWidget(rows, 3)
            table.setHorizontalHeaderLabels(
                ["Layer", "Band", self.result["reducer"].title()]
            )
            self._populate_multi_table(table)
            table.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.ResizeMode.Stretch
            )
            table.horizontalHeader().setSectionResizeMode(
                1, QHeaderView.ResizeMode.ResizeToContents
            )
            table.horizontalHeader().setSectionResizeMode(
                2, QHeaderView.ResizeMode.ResizeToContents
            )
        else:
            table = QTableWidget(len(self.result["values"]), 2)
            table.setHorizontalHeaderLabels(["Band", self.result["reducer"].title()])
            self._populate_single_table(table)
            table.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.ResizeMode.Stretch
            )
            table.horizontalHeader().setSectionResizeMode(
                1, QHeaderView.ResizeMode.ResizeToContents
            )

        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)
        return table

    def _populate_single_table(self, table: QTableWidget) -> None:
        for row, (band, value) in enumerate(self.result["values"].items()):
            table.setItem(row, 0, QTableWidgetItem(str(band)))
            table.setItem(row, 1, QTableWidgetItem(self._format_value(value)))

    def _populate_multi_table(self, table: QTableWidget) -> None:
        row = 0
        for layer_result in self.results:
            if not layer_result["values"]:
                table.setItem(row, 0, QTableWidgetItem(layer_result["layer"]))
                table.setItem(row, 1, QTableWidgetItem(""))
                table.setItem(row, 2, QTableWidgetItem("No data"))
                row += 1
                continue
            for band, value in layer_result["values"].items():
                table.setItem(row, 0, QTableWidgetItem(layer_result["layer"]))
                table.setItem(row, 1, QTableWidgetItem(str(band)))
                table.setItem(row, 2, QTableWidgetItem(self._format_value(value)))
                row += 1

    def _populate_feature_table(self, table: QTableWidget) -> None:
        row = 0
        for feature_info in self.result["features"]:
            properties = feature_info.get("properties", {})
            feature_id = str(feature_info.get("id", ""))
            if not properties:
                table.setItem(row, 0, QTableWidgetItem(feature_id))
                table.setItem(row, 1, QTableWidgetItem(""))
                table.setItem(row, 2, QTableWidgetItem("No properties"))
                row += 1
                continue
            for property_name, value in properties.items():
                table.setItem(row, 0, QTableWidgetItem(feature_id))
                table.setItem(row, 1, QTableWidgetItem(str(property_name)))
                table.setItem(row, 2, QTableWidgetItem(self._format_value(value)))
                row += 1

    def _geometry_text(self) -> str:
        geometry = self.result["geometry"]
        if self.result["selection_type"] == "point":
            return f"{geometry['longitude']:.6f}, {geometry['latitude']:.6f}"
        return (
            f"{geometry['west']:.6f}, {geometry['south']:.6f} to "
            f"{geometry['east']:.6f}, {geometry['north']:.6f}"
        )

    @staticmethod
    def _format_value(value: Any) -> str:
        return _format_identify_value(value)

    def _button_clicked(self, button) -> None:
        if self.sender().standardButton(button) == QDialogButtonBox.StandardButton.Save:
            self.add_results_layer()

    def add_results_layer(self) -> None:
        try:
            layer = add_identify_results_layer(self.result)
        except (OSError, TypeError, ValueError) as error:
            QMessageBox.critical(self, "Could not add layer", str(error))
            return

        QMessageBox.information(
            self,
            "Layer added",
            f"Identify results added as temporary layer:\n{layer.name()}",
        )


class EarthEngineIdentifyTool(QgsMapTool):
    """Identify pixels, regions, and features from Earth Engine layers."""

    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super().__init__(self.canvas)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.start_point = None
        self.start_pos = None

        self.rubber_band = QgsRubberBand(self.canvas, Qgis.GeometryType.Polygon)
        self.rubber_band.setColor(QColor(255, 193, 7))
        self.rubber_band.setFillColor(QColor(255, 193, 7, 40))
        self.rubber_band.setWidth(2)

        self.point_marker = QgsVertexMarker(self.canvas)
        self.point_marker.setColor(QColor(255, 193, 7))
        self.point_marker.setFillColor(QColor(255, 255, 255))
        icon_type = getattr(
            getattr(QgsVertexMarker, "IconType", QgsVertexMarker), "ICON_CROSS"
        )
        self.point_marker.setIconType(icon_type)
        self.point_marker.setIconSize(14)
        self.point_marker.setPenWidth(3)
        self.point_marker.hide()

    def canvasPressEvent(self, event: QgsMapMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self.clear_highlight()
        self.start_point = event.mapPoint()
        self.start_pos = event.pos()

    def canvasMoveEvent(self, event: QgsMapMouseEvent) -> None:
        if self.start_point is None or not (
            event.buttons() & Qt.MouseButton.LeftButton
        ):
            return
        if not self._is_drag(event.pos()):
            return
        self._show_rectangle(self.start_point, event.mapPoint())

    def canvasReleaseEvent(self, event: QgsMapMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton or self.start_point is None:
            return

        start_point = self.start_point
        is_drag = self._is_drag(event.pos())
        self.start_point = None
        self.start_pos = None

        if is_drag:
            rectangle = QgsRectangle(start_point, event.mapPoint())
            self._show_rectangle(start_point, event.mapPoint())
            self._identify(rectangle)
        else:
            self.point_marker.setCenter(start_point)
            self.point_marker.show()
            self._identify(start_point)

    def deactivate(self) -> None:
        self.start_point = None
        self.start_pos = None
        self.clear_highlight()
        super().deactivate()

    def clear_highlight(self) -> None:
        self.rubber_band.reset(Qgis.GeometryType.Polygon)
        self.point_marker.hide()

    def _is_drag(self, position) -> bool:
        if self.start_pos is None:
            return False
        delta = position - self.start_pos
        return delta.manhattanLength() >= QApplication.startDragDistance()

    def _show_rectangle(self, start: QgsPointXY, end: QgsPointXY) -> None:
        geometry = QgsGeometry.fromRect(QgsRectangle(start, end))
        self.rubber_band.setToGeometry(geometry, None)

    def _identify(self, selection) -> None:
        is_region = isinstance(selection, QgsRectangle)

        layers = self._identify_layers()
        if not layers:
            self.iface.messageBar().pushMessage(
                "Earth Engine Identify",
                "Select one or more Earth Engine layers before identifying.",
                level=Qgis.MessageLevel.Warning,
                duration=5,
            )
            return

        try:
            selection_context = self._selection_context(selection, is_region)
            reducer = identify_reducer(is_region)
            reducer_name = identify_reducer_name(is_region)

            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                results = self._identify_layer_results(
                    layers, selection_context, reducer, reducer_name, is_region
                )
            finally:
                QApplication.restoreOverrideCursor()
        except Exception as error:
            self.iface.messageBar().pushMessage(
                "Earth Engine Identify",
                f"Could not identify the selection: {error}",
                level=Qgis.MessageLevel.Critical,
                duration=8,
            )
            return

        result = results[0] if len(results) == 1 else self._multi_result(results)
        IdentifyResultsDialog(result, self.iface.mainWindow()).exec()

    def _identify_layers(self) -> List[Any]:
        return [
            layer
            for layer in self._selected_layer_tree_layers()
            if utils.is_ee_raster_layer(layer)
            or utils.is_ee_feature_collection_layer(layer)
        ]

    def _selected_layer_tree_layers(self) -> List[Any]:
        try:
            layer_tree_view = self.iface.layerTreeView()
        except Exception:
            return []

        try:
            selected_layers = layer_tree_view.selectedLayers()
            if selected_layers:
                return list(selected_layers)
        except Exception:
            pass

        try:
            selected_nodes = layer_tree_view.selectedLayerNodes()
        except Exception:
            return []

        layers = []
        for node in selected_nodes:
            layer = node.layer() if hasattr(node, "layer") else None
            if layer is not None:
                layers.append(layer)
        return layers

    def _selection_context(self, selection, is_region: bool) -> Dict[str, Any]:
        transform = QgsCoordinateTransform(
            self.canvas.mapSettings().destinationCrs(),
            QgsCoordinateReferenceSystem("EPSG:4326"),
            QgsProject.instance(),
        )
        scale = Map.getScale()
        if is_region:
            coordinates = rectangle_to_wgs84_coordinates(selection, transform)
            ee_geometry = ee.Geometry.Polygon([coordinates], "EPSG:4326", False)
            feature_geometry = QgsGeometry.fromPolygonXY(
                [[QgsPointXY(x, y) for x, y in coordinates]]
            )
            xs = [coordinate[0] for coordinate in coordinates]
            ys = [coordinate[1] for coordinate in coordinates]
            geometry_metadata = {
                "west": min(xs),
                "south": min(ys),
                "east": max(xs),
                "north": max(ys),
            }
        else:
            point_wgs84 = transform.transform(selection)
            ee_geometry = point_to_ee_geometry(point_wgs84)
            feature_geometry = QgsGeometry.fromPointXY(point_wgs84)
            geometry_metadata = {
                "longitude": point_wgs84.x(),
                "latitude": point_wgs84.y(),
            }

        return {
            "ee_geometry": ee_geometry,
            "feature_geometry": feature_geometry,
            "geometry": geometry_metadata,
            "scale": scale,
        }

    def _identify_layer_results(
        self,
        layers: List[Any],
        selection_context: Dict[str, Any],
        reducer: ee.Reducer,
        reducer_name: str,
        is_region: bool,
    ) -> List[Dict[str, Any]]:
        results = []
        for layer in layers:
            feature_collection = utils.get_ee_feature_collection_from_layer(layer)
            if feature_collection is not None:
                features = identify_features(
                    feature_collection,
                    selection_context["ee_geometry"],
                )
                results.append(
                    {
                        "result_type": "features",
                        "layer": layer.name(),
                        "selection_type": "region" if is_region else "point",
                        "geometry": selection_context["geometry"],
                        "feature_geometry": selection_context["feature_geometry"],
                        "features": features,
                    }
                )
                continue

            image = utils.get_ee_object_from_layer(layer)
            if image is None:
                raise ValueError(
                    f"The Earth Engine image could not be restored from {layer.name()}."
                )

            values = identify_image(
                image,
                selection_context["ee_geometry"],
                selection_context["scale"],
                reducer,
            )
            results.append(
                {
                    "layer": layer.name(),
                    "selection_type": "region" if is_region else "point",
                    "reducer": reducer_name,
                    "scale": selection_context["scale"],
                    "geometry": selection_context["geometry"],
                    "feature_geometry": selection_context["feature_geometry"],
                    "values": values,
                }
            )
        return results

    @staticmethod
    def _multi_result(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        first = results[0]
        if all(result.get("result_type") == "features" for result in results):
            features = []
            for result in results:
                for feature_info in result["features"]:
                    feature_info = dict(feature_info)
                    feature_info["_source_layer"] = result["layer"]
                    features.append(feature_info)
            return {
                "result_type": "features",
                "layer": "Earth Engine identify",
                "selection_type": first["selection_type"],
                "geometry": first["geometry"],
                "feature_geometry": first["feature_geometry"],
                "features": features,
            }
        if any(result.get("result_type") == "features" for result in results):
            raise ValueError(
                "Identify feature collection layers separately from raster layers."
            )
        return {
            "results": results,
            "selection_type": first["selection_type"],
            "reducer": first["reducer"],
            "scale": first["scale"],
            "geometry": first["geometry"],
            "feature_geometry": first["feature_geometry"],
        }
