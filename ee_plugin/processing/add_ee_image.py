import json
import logging
from typing import Any, Dict, Optional

import ee
from qgis.PyQt.QtWidgets import QVBoxLayout, QFormLayout, QLabel, QLineEdit, QComboBox
from qgis.PyQt.QtCore import QTimer
from qgis.gui import QgsCollapsibleGroupBox
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterString,
    QgsProcessingException,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingOutputRasterLayer,
    QgsProcessingOutputString,
    QgsGradientColorRamp,
    QgsColorBrewerColorRamp,
    QgsLimitedRandomColorRamp,
    QgsPresetSchemeColorRamp,
    QgsCptCityColorRamp,
)

from ..Map import addLayer
from ..logging import local_context
from ..ui.widgets import VisualizationParamsWidget
from ..utils import get_available_bands
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

        self.viz_widget = VisualizationParamsWidget()
        viz_group = QgsCollapsibleGroupBox("Visualization Parameters")
        viz_group.setCollapsed(False)
        viz_layout = QVBoxLayout()
        viz_layout.addWidget(self.viz_widget)
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
            return {
                "IMAGE_ID": image_id,
                "VIZ_PARAMS": json.dumps(self._serialize_viz_params(viz_params)),
            }
        except Exception as e:
            raise ValueError(f"Invalid parameters: {e}")

    def _serialize_viz_params(self, viz_params):
        result = {}
        k = "palette"
        if "palette" in viz_params:
            v = viz_params[k]
            if isinstance(v, QgsGradientColorRamp):
                result[k] = [stop.color.name() for stop in v.stops()]
            elif isinstance(v, QgsColorBrewerColorRamp):
                result[k] = [v.color(i).name() for i in range(v.count())]
            elif isinstance(v, QgsLimitedRandomColorRamp):
                count = v.count()  # only generate the number of defined colors
                result[k] = [v.color(i).name() for i in range(count)]
            elif isinstance(v, QgsPresetSchemeColorRamp):
                result[k] = [c.name() for c in v.colors()]
            elif isinstance(v, QgsCptCityColorRamp):
                result[k] = [c.name() for c in v.colors()]
            else:
                logger.warning(
                    f"Unsupported color ramp type: {type(v)}. Defaulting to empty color ramp."
                )
                result[k] = []  # fallback, or raise error if needed
        return result


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
        logger.info(
            f"[DEBUG] Parameters received: IMAGE_ID={image_id}, VIZ_PARAMS={viz_params_raw}"
        )

        if not image_id:
            raise QgsProcessingException("Image ID is required.")

        try:
            asset_info = ee.data.getAsset(image_id)
            asset_type = asset_info.get("type", "")

            if asset_type == "IMAGE":
                ee_object = ee.Image(image_id)
            else:
                raise QgsProcessingException(f"Unsupported asset type: {asset_type}")

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
