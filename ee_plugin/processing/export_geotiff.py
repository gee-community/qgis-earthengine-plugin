import os
import logging

# --- new imports for dialog and typing ---
from typing import List, Optional

from qgis import gui
from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QHBoxLayout,
    QLineEdit,
    QFileDialog,
)

from .custom_algorithm_dialog import BaseAlgorithmDialog

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterExtent,
    QgsProcessingParameterNumber,
    QgsProcessingParameterCrs,
    QgsProcessingParameterFileDestination,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterEnum,
    QgsCoordinateReferenceSystem,
    QgsProcessingParameterString,
    QgsCoordinateTransform,
    QgsProject,
)

from ..logging import local_context
from .. import Map
from ..utils import ee_image_to_geotiff


logging = logging.getLogger(__name__)


class ExportGeoTIFFAlgorithmDialog(BaseAlgorithmDialog):
    """Custom dialog that adds a dynamic bands selector for the chosen EE image."""

    def __init__(
        self, algorithm: QgsProcessingAlgorithm, parent: Optional[QWidget] = None
    ):
        self._raster_layers: List[str] = [
            layer.name()
            for layer in Map.get_iface().mapCanvas().layers()
            if layer.providerType() == "EE"
        ]
        self._bands_cache: dict[str, List[str]] = {}
        super().__init__(algorithm, parent=parent, title="Export Image to GeoTIFF")

    def buildDialog(self) -> QVBoxLayout:
        layout = QVBoxLayout()

        # --- Source image selector ---
        form = QFormLayout()
        self.ee_image_combo = QComboBox(objectName="EE_IMAGE")
        self.ee_image_combo.addItems(self._raster_layers)
        self.ee_image_combo.currentIndexChanged.connect(self._on_image_changed)
        form.addRow(QLabel("EE Image"), self.ee_image_combo)

        # --- Scale ---
        self.scale_edit = QLineEdit(objectName="SCALE")
        self.scale_edit.setText("100")
        form.addRow(QLabel("Scale (meters)"), self.scale_edit)

        # --- Projection (use native widget) ---
        self.proj_widget = gui.QgsProjectionSelectionWidget()
        self.proj_widget.setCrs(QgsCoordinateReferenceSystem.fromEpsgId(4326))
        form.addRow(QLabel("Projection"), self.proj_widget)

        layout.addLayout(form)

        # --- Extent group ---
        self.extent_group = gui.QgsExtentGroupBox(
            objectName="EXTENT",
            title="Extent",
            collapsed=False,
        )
        # Keep extent output CRS synced with the chosen projection
        self.extent_group.setOutputCrs(self.proj_widget.crs())
        try:
            self.proj_widget.crsChanged.connect(self.extent_group.setOutputCrs)
        except Exception:
            # Older QGIS may not emit crsChanged on this widget; ignore if unavailable
            pass
        self.extent_group.setMapCanvas(Map.get_iface().mapCanvas())
        # As a final safeguard, clear any pre-filled line edits inside the extent widget
        try:
            for le in self.extent_group.findChildren(QLineEdit):
                le.clear()
        except Exception:
            pass
        layout.addWidget(self.extent_group)

        # --- Bands selector ---
        bands_form = QFormLayout()
        bands_form.addRow(QLabel("Select bands to export (order preserved)"))
        bands_row = QHBoxLayout()
        self.available_list = QListWidget(objectName="available_bands")
        self.selected_list = QListWidget(objectName="selected_bands")
        self.available_list.setSelectionMode(QListWidget.MultiSelection)
        self.selected_list.setSelectionMode(QListWidget.MultiSelection)

        btns_col = QVBoxLayout()
        self.add_btn = QPushButton(">>")
        self.remove_btn = QPushButton("<<")
        self.up_btn = QPushButton("▲")
        self.down_btn = QPushButton("▼")
        btns_col.addWidget(self.add_btn)
        btns_col.addWidget(self.remove_btn)
        btns_col.addWidget(self.up_btn)
        btns_col.addWidget(self.down_btn)

        self.add_btn.clicked.connect(self._move_right)
        self.remove_btn.clicked.connect(self._move_left)
        self.up_btn.clicked.connect(lambda: self._move_selected(-1))
        self.down_btn.clicked.connect(lambda: self._move_selected(1))

        bands_row.addWidget(self.available_list)
        bands_row.addLayout(btns_col)
        bands_row.addWidget(self.selected_list)
        bands_form.addRow(bands_row)
        layout.addLayout(bands_form)

        # --- Output path ---
        out_row = QHBoxLayout()
        self.output_edit = QLineEdit(objectName="OUTPUT")
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_output)
        out_row.addWidget(self.output_edit)
        out_row.addWidget(browse_btn)
        form2 = QFormLayout()
        form2.addRow(QLabel("Output File (.tif)"), out_row)
        layout.addLayout(form2)

        # Initialize bands for the first selected layer
        self._on_image_changed()

        return layout

    # --- helpers ---
    def _browse_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save GeoTIFF", "", "GeoTIFF (*.tif)"
        )
        if path:
            if not path.lower().endswith(".tif"):
                path += ".tif"
            self.output_edit.setText(path)

    def _on_image_changed(self):
        name = self.ee_image_combo.currentText()
        if not name:
            return
        bands = self._bands_cache.get(name)
        if bands is None:
            # look up layer and query band names from ee.Image
            layer = next(
                (
                    layer
                    for layer in Map.get_iface().mapCanvas().layers()
                    if layer.name() == name and layer.providerType() == "EE"
                ),
                None,
            )
            if layer is None:
                bands = []
            else:
                try:
                    ee_image = layer.dataProvider().ee_object
                    bands = ee_image.bandNames().getInfo() or []
                except Exception:
                    bands = []
            self._bands_cache[name] = bands
        self.available_list.clear()
        self.selected_list.clear()
        for b in bands:
            self.available_list.addItem(QListWidgetItem(b))

    def _move_right(self):
        for item in list(self.available_list.selectedItems()):
            self.selected_list.addItem(QListWidgetItem(item.text()))
            self.available_list.takeItem(self.available_list.row(item))

    def _move_left(self):
        for item in list(self.selected_list.selectedItems()):
            self.available_list.addItem(QListWidgetItem(item.text()))
            self.selected_list.takeItem(self.selected_list.row(item))

    def _move_selected(self, direction: int):
        # Move in selected_list only
        current_rows = sorted(
            {self.selected_list.row(i) for i in self.selected_list.selectedItems()}
        )
        if not current_rows:
            return
        if direction > 0:
            current_rows = reversed(current_rows)
        for row in current_rows:
            new_row = row + direction
            if 0 <= new_row < self.selected_list.count():
                item = self.selected_list.takeItem(row)
                self.selected_list.insertItem(new_row, item)
                item.setSelected(True)

    def getParameters(self) -> dict:
        # Build parameters dictionary matching algorithm's keys
        params = {
            "EE_IMAGE": max(self.ee_image_combo.currentIndex(), 0),
            "SCALE": float(self.scale_edit.text()) if self.scale_edit.text() else 100.0,
            "PROJECTION": self.proj_widget.crs().authid(),
            "EXTENT": self.extent_group.outputExtent(),
            "BANDS": ",".join(self._selected_bands()),
            "OUTPUT": self.output_edit.text(),
        }
        return params

    def _selected_bands(self) -> List[str]:
        return [
            self.selected_list.item(i).text() for i in range(self.selected_list.count())
        ]

    # Hook called by BaseAlgorithmDialog when user presses Cancel
    def onCancelRequested(self):
        try:
            alg = self.algorithm()
        except Exception:
            alg = None
        # Try to cancel a v1 operations export if the algorithm stored its name
        try:
            if alg is not None and getattr(alg, "_ee_operation_name", None):
                import ee

                ee.data.cancelOperation(alg._ee_operation_name)
                local_context.pushInfo(
                    f"Requested cancel of EE operation: {alg._ee_operation_name}"
                )
        except Exception:
            pass
        # Try to cancel an old ee.batch.Task if present
        try:
            if alg is not None and getattr(alg, "_ee_task", None):
                alg._ee_task.cancel()
                local_context.pushInfo("Requested cancel of EE batch task")
        except Exception:
            pass


class ExportGeoTIFFAlgorithm(QgsProcessingAlgorithm):
    """Export an EE Image to a GeoTIFF file."""

    OUTPUT = "OUTPUT"

    def initAlgorithm(self, config: dict) -> None:
        raster_layers = [
            layer.name()
            for layer in Map.get_iface().mapCanvas().layers()
            if layer.providerType() == "EE"
        ]

        if not raster_layers:
            logging.warning(
                "No EE layers found in the current project. Please load an EE layer to use this algorithm."
            )
        self.raster_layers = raster_layers
        self.addParameter(
            QgsProcessingParameterEnum(
                "EE_IMAGE", "EE Image Name", options=raster_layers, optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterExtent(
                "EXTENT", "Extent", defaultValue=None, optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber("SCALE", "Scale (meters)", defaultValue=100)
        )
        self.addParameter(
            QgsProcessingParameterCrs(
                "PROJECTION", "Projection", defaultValue="EPSG:4326"
            )
        )
        # --- Bands parameter (inserted here) ---
        self.addParameter(
            QgsProcessingParameterString(
                "BANDS",
                "Bands to export (comma-separated)",
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT, "Output File", fileFilter="GeoTIFF (*.tif);;All Files (*)"
            )
        )

    def processAlgorithm(
        self,
        parameters: dict,
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict:
        # add logs to algorithm dialog
        local_context.set_feedback(feedback)
        feedback.pushInfo("Validating parameters…")
        selected_index = self.parameterAsEnum(parameters, "EE_IMAGE", context)
        ee_img = self.raster_layers[selected_index]
        rect = self.parameterAsExtent(parameters, "EXTENT", context)
        rect_source_crs = self.parameterAsExtentCrs(parameters, "EXTENT", context)
        if (
            (rect is None)
            or (hasattr(rect, "isEmpty") and rect.isEmpty())
            or (hasattr(rect, "isValid") and not rect.isValid())
            or (hasattr(rect, "toString") and rect.toString() == "Null")
        ):
            raise ValueError(
                "Extent is not set. Please choose an extent (Map Canvas, Draw, or Layer) before exporting."
            )

        target_crs = self.parameterAsCrs(parameters, "PROJECTION", context)

        if rect_source_crs != target_crs:
            tr = QgsCoordinateTransform(
                rect_source_crs, target_crs, QgsProject.instance()
            )
            rect = tr.transformBoundingBox(rect)

        extent = [rect.xMinimum(), rect.yMinimum(), rect.xMaximum(), rect.yMaximum()]
        scale = self.parameterAsDouble(parameters, "SCALE", context)
        projection = self.parameterAsCrs(parameters, "PROJECTION", context).authid()
        out_path = self.parameterAsFile(parameters, "OUTPUT", context)
        if feedback.isCanceled():
            raise RuntimeError("Canceled")

        layer = next(
            (
                layer
                for layer in Map.get_iface().mapCanvas().layers()
                if layer.name() == ee_img and layer.providerType() == "EE"
            ),
            None,
        )

        if not layer:
            msg = f"Layer {ee_img} not found"
            raise ValueError(msg)

        ee_image = layer.dataProvider().ee_object

        # Optional band selection
        bands_param = parameters.get("BANDS")
        if bands_param:
            try:
                bands_list = [b.strip() for b in bands_param.split(",") if b.strip()]
                if bands_list:
                    ee_image = ee_image.select(bands_list)
            except Exception as e:
                raise ValueError(f"Invalid bands selection '{bands_param}': {e}")

        tile_dir = os.path.dirname(out_path)
        if tile_dir == "":
            tile_dir = os.getcwd()
        base_name = os.path.splitext(os.path.basename(out_path))[0]

        feedback.pushInfo("Starting EE export to GeoTIFF…")

        if feedback.isCanceled():
            raise RuntimeError("Canceled")

        handle = ee_image_to_geotiff(
            ee_image=ee_image,
            extent=extent,
            scale=scale,
            projection=projection,
            out_dir=tile_dir,
            base_name=base_name,
            merge_output=out_path,
            feedback=feedback,
        )

        # If the helper returns an EE operation or task, keep a reference for cancel
        try:
            if isinstance(handle, dict) and "name" in handle:
                # v1 operation dict {"name": "operations/XYZ"}
                self._ee_operation_name = handle.get("name")
            elif hasattr(handle, "id") or hasattr(handle, "task_type"):
                # ee.batch.Task-like
                self._ee_task = handle
        except Exception:
            pass

        feedback.pushInfo("Export complete.")
        return {self.OUTPUT: out_path}

    def name(self) -> str:
        return "export_geotiff"

    def displayName(self) -> str:
        return "Export Image to GeoTIFF"

    def group(self) -> str:
        return "Export"

    def groupId(self) -> str:
        return "export"

    def createInstance(self) -> QgsProcessingAlgorithm:
        return ExportGeoTIFFAlgorithm()

    def shortHelpString(self) -> str:
        return (
            "<h2>Export Earth Engine Image to GeoTIFF</h2>"
            "<p>This tool allows you to export an Earth Engine image already loaded into a project to a GeoTIFF format. You must specify:</p>"
            "<ul>"
            "<li><b>Extent</b>: Coordinates defining the current map extent for the export region.</li>"
            "<li><b>Scale</b>: Resolution in meters per pixel.</li>"
            "<li><b>Projection</b>: Target projection for the exported image (e.g., EPSG:4326).</li>"
            "<li><b>Bands</b>: Select which bands to export (optional).</li>"
            "<li><b>Output File</b>: Destination path for the exported GeoTIFF file.</li>"
            "</ul>"
        )

    def createCustomParametersWidget(self, parent=None):
        return ExportGeoTIFFAlgorithmDialog(algorithm=self, parent=parent)
