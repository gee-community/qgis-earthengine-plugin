import json
import logging
from typing import Any, Dict, Optional

import ee
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterString,
    QgsProcessingException,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingOutputRasterLayer,
    QgsProcessingOutputString,
)

from ..Map import addLayer
from ..feedback_context import set_feedback

logger = logging.getLogger(__name__)


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

    def processAlgorithm(
        self,
        parameters: Dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> Dict[str, Any]:
        # add logs to algorithm dialog
        set_feedback(feedback)
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
        return "Add EE Image"

    def group(self) -> str:
        return "Add Layer"

    def groupId(self) -> str:
        return "add_layer"

    def shortHelpString(self) -> str:
        return (
            "<b>Add EE Image</b><br><br>"
            "Loads a Google Earth Engine image into QGIS.<br><br>"
            "<b>Example Image ID:</b><br>"
            "<code>USGS/SRTMGL1_003</code><br><br>"
            "<b>Example Visualization Parameters (JSON):</b><br>"
            '<pre>{"min": 0, "max": 3000, "palette": ["#000000", "#ffffff"]}</pre>'
            "<b>Earth Engine Data Catalog:</b><br>"
            "<a href='https://developers.google.com/earth-engine/datasets'>https://developers.google.com/earth-engine/datasets</a>"
        )

    def createInstance(self) -> "AddEEImageAlgorithm":
        return AddEEImageAlgorithm()
