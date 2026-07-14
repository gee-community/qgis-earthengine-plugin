"""Map tool for identifying pixel values in Earth Engine raster layers."""

import re
from typing import Any, Dict, Optional

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


class IdentifyResultsDialog(QDialog):
    """Display and add Earth Engine identify results to the project."""

    def __init__(self, result: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.result = result
        self.setWindowTitle(f"Earth Engine Identify - {result['layer']}")
        self.setMinimumSize(480, 360)

        layout = QVBoxLayout(self)

        heading = (
            "Region statistics"
            if result["selection_type"] == "region"
            else "Pixel values"
        )
        title = QLabel(f"<h2 style='margin: 0'>{heading}</h2>")
        subtitle = QLabel(
            "Mean value for each band in the selected area."
            if result["selection_type"] == "region"
            else "First unmasked value for each band at the selected point."
        )
        subtitle.setStyleSheet("color: palette(mid); margin-bottom: 8px;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        details = QFormLayout()
        details.addRow("Layer", QLabel(result["layer"]))
        details.addRow("Scale", QLabel(f"{result['scale']:.3f} m"))
        details.addRow("Selection", QLabel(self._geometry_text()))
        layout.addLayout(details)

        table = QTableWidget(len(result["values"]), 2)
        table.setHorizontalHeaderLabels(["Band", result["reducer"].title()])
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        for row, (band, value) in enumerate(result["values"].items()):
            table.setItem(row, 0, QTableWidgetItem(str(band)))
            table.setItem(row, 1, QTableWidgetItem(self._format_value(value)))
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        table.setSortingEnabled(True)
        layout.addWidget(table)

        if not result["values"]:
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
        if value is None:
            return "No data"
        if isinstance(value, float):
            return f"{value:.8g}"
        return str(value)

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
    """Identify pixels or dragged regions from an Earth Engine raster layer."""

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

        layer = self.iface.activeLayer()
        if not utils.is_ee_raster_layer(layer):
            self.iface.messageBar().pushMessage(
                "Earth Engine Identify",
                "Select an Earth Engine raster layer before identifying.",
                level=Qgis.MessageLevel.Warning,
                duration=5,
            )
            return

        image = utils.get_ee_object_from_layer(layer)
        if image is None:
            self.iface.messageBar().pushMessage(
                "Earth Engine Identify",
                "The Earth Engine image could not be restored from this layer.",
                level=Qgis.MessageLevel.Critical,
                duration=5,
            )
            return

        try:
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
            reducer = identify_reducer(is_region)
            reducer_name = identify_reducer_name(is_region)

            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                values = identify_image(image, ee_geometry, scale, reducer)
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

        result = {
            "layer": layer.name(),
            "selection_type": "region" if is_region else "point",
            "reducer": reducer_name,
            "scale": scale,
            "geometry": geometry_metadata,
            "feature_geometry": feature_geometry,
            "values": values,
        }
        IdentifyResultsDialog(result, self.iface.mainWindow()).exec()
