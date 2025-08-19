import json
import logging
from typing import Any, Dict, Optional

import ee
from qgis.PyQt.QtWidgets import (
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QCheckBox,
)
from qgis.PyQt.QtCore import QTimer
from qgis.gui import QgsCollapsibleGroupBox
from qgis import gui
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterString,
    QgsProcessingException,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingOutputRasterLayer,
    QgsProcessingOutputString,
    QgsProcessingParameterExtent,
    QgsProcessingParameterBoolean,
)

from ..Map import addLayer
from .. import Map
from ..logging import local_context
from ..ui.widgets import VisualizationParamsWidget
from ..utils import get_available_bands, get_ee_extent
from ..ui.utils import serialize_color_ramp
from .custom_algorithm_dialog import BaseAlgorithmDialog

logger = logging.getLogger(__name__)


class AddImageAlgorithmDialog(BaseAlgorithmDialog):
    def __init__(self, algorithm: QgsProcessingAlgorithm, parent=None):
        super().__init__(algorithm, parent=parent, title="Add EE Image")
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._on_image_id_ready)

    def buildDialog(self):
        layout = QVBoxLayout(self)

        self.image_id_input = QLineEdit()
        self.image_id_input.setObjectName("image_id_input")
        self.image_id_input.setToolTip("Enter the Earth Engine Image ID.")
        self.image_id_input.textChanged.connect(self._on_image_id_changed)

        source_form = QFormLayout()
        source_form.addRow(
            QLabel("Image ID (e.g. USGS/SRTMGL1_003)"), self.image_id_input
        )
        layout.addLayout(source_form)

        # Extent controls (optional)
        self.extent_group = gui.QgsExtentGroupBox(
            objectName="extent",
            title="Filter by Extent (Bounds)",
            collapsed=True,
        )
        self.extent_group.setMapCanvas(Map.get_iface().mapCanvas())
        self.extent_group.setToolTip("Specify the geographic extent.")
        layout.addWidget(self.extent_group)

        # visualization group
        self.viz_widget = VisualizationParamsWidget()
        viz_group = QgsCollapsibleGroupBox("Visualization Parameters")
        viz_group.setCollapsed(False)
        viz_layout = QVBoxLayout()
        viz_layout.addWidget(self.viz_widget)
        # Insert clip checkbox
        self.clip_checkbox = QCheckBox(
            "Clip to Extent",
            checked=True,
            toolTip=("Whether to clip the final image to the specified extent."),
        )
        viz_layout.addWidget(self.clip_checkbox)
        viz_group.setLayout(viz_layout)
        layout.addWidget(viz_group)

        return layout

    def _on_image_id_changed(self):
        self._update_timer.start(500)

    def _on_image_id_ready(self):
        self.update_band_dropdowns()

    def update_band_dropdowns(self):
        bands = (
            get_available_bands(self.image_id_input.text().strip(), silent=True) or []
        )
        for i in range(3):
            combo = self.viz_widget.findChild(QComboBox, f"viz_band_{i}")
            current = combo.currentText()
            combo.clear()
            combo.addItems(bands)
            combo.setCurrentText(current)

    def getParameters(self):
        try:
            image_id = self.image_id_input.text().strip()
            viz_params = self.viz_widget.get_viz_params()
            viz_data = viz_params.copy()
            serialized = serialize_color_ramp(viz_params)
            if "palette" in serialized and serialized["palette"]:
                viz_data["palette"] = serialized["palette"]
            return {
                "IMAGE_ID": image_id,
                "VIZ_PARAMS": json.dumps(viz_data),
                "EXTENT": self.extent_group.outputExtent(),
                "EXTENT_CRS": self.extent_group.outputCrs(),
                "CLIP_TO_EXTENT": self.clip_checkbox.isChecked(),
            }
        except Exception as e:
            raise ValueError(f"Invalid parameters: {e}")


class AddEEImageAlgorithm(QgsProcessingAlgorithm):
    def initAlgorithm(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.addParameter(
            QgsProcessingParameterString(
                "IMAGE_ID",
                "GEE Image ID",
                optional=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "VIZ_PARAMS",
                "Visualization Parameters (JSON)",
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterExtent(
                "EXTENT",
                "Extent",
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                "CLIP_TO_EXTENT",
                "Clip to extent",
                defaultValue=True,
            )
        )
        self.addOutput(QgsProcessingOutputRasterLayer("OUTPUT", "EE Image"))
        self.addOutput(QgsProcessingOutputString("LAYER_NAME", "Layer Name"))

    def createCustomParametersWidget(self, parent=None):
        return AddImageAlgorithmDialog(self, parent=parent)

    def processAlgorithm(
        self,
        parameters: Dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> Dict[str, Any]:
        # add logs to algorithm dialog
        local_context.set_feedback(feedback)
        image_id = self.parameterAsString(parameters, "IMAGE_ID", context)
        viz_params_raw = self.parameterAsString(parameters, "VIZ_PARAMS", context)
        extent = parameters.get("EXTENT")
        extent_crs = parameters.get("EXTENT_CRS")
        clip_to_extent = parameters.get("CLIP_TO_EXTENT", True)

        if not image_id:
            raise QgsProcessingException("Image ID is required.")

        try:
            asset_info = ee.data.getAsset(image_id)
            asset_type = asset_info.get("type", "")

            if asset_type == "IMAGE":
                ee_object = ee.Image(image_id)
            else:
                raise QgsProcessingException(f"Unsupported asset type: {asset_type}")

            ee_extent = None
            if extent and extent_crs:
                try:
                    ee_extent = get_ee_extent(extent, extent_crs, context.project())
                except Exception as e:
                    logger.warning(f"Invalid extent provided; ignoring. Error: {e}")
            elif extent and not extent_crs:
                logger.warning("Extent provided without CRS; ignoring extent.")

            if clip_to_extent and ee_extent is not None:
                ee_object = ee_object.clip(ee_extent)

            if viz_params_raw:
                try:
                    viz_params = json.loads(viz_params_raw.replace("'", '"'))
                except json.JSONDecodeError:
                    raise QgsProcessingException(
                        "Invalid JSON format in visualization parameters."
                    )
            else:
                viz_params = {}

            layer = addLayer(ee_object, viz_params, image_id)

            if not layer:
                raise QgsProcessingException("Failed to add EE layer to map.")

            return {"OUTPUT": layer.id(), "LAYER_NAME": layer.name()}

        except ee.EEException as e:
            raise QgsProcessingException(f"Earth Engine Error: {str(e)}")

        except Exception as e:
            raise QgsProcessingException(f"Unexpected error: {str(e)}")

    def name(self) -> str:
        return "add_ee_image"

    def displayName(self) -> str:
        return "Add Image"

    def group(self) -> str:
        return "Add Layer"

    def groupId(self) -> str:
        return "add_layer"

    def shortHelpString(self) -> str:
        return """
            <html>
            <b>Add EE Image</b><br>
            This algorithm adds a single Earth Engine image to the map using the specified visualization parameters.<br><br>
 
            <h3>Parameters:</h3>
            <ul>
                <li><b>Image ID:</b> The Earth Engine <a href='https://developers.google.com/earth-engine/guides/manage_assets'>Asset ID</a> to add to the map (e.g. <code>USGS/SRTMGL1_003</code>).</li>
                <li><b>Visualization Parameters:</b> These include <code>min</code>, <code>max</code>, <code>bands</code>, <code>palette</code> (for single-band images), and <code>gamma</code> (for RGB or multi-band images).<br>
                Important: <code>gamma</code> and <code>palette</code> cannot be used together. Use <code>palette</code> only for single-band visualizations.<br>
                See the <a href='https://developers.google.com/earth-engine/guides/image_visualization' target='_blank'>Image Visualization Guide</a> for details.
                </li>
            </ul>
 
            <b>Earth Engine Data Catalog:</b><br>
            <a href='https://developers.google.com/earth-engine/datasets'>https://developers.google.com/earth-engine/datasets</a>
            </html>
            """

    def createInstance(self) -> "AddEEImageAlgorithm":
        return AddEEImageAlgorithm()
