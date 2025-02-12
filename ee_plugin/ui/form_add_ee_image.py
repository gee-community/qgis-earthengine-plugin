import json
from typing import Dict

import ee
from qgis import gui
from qgis.PyQt import QtWidgets
from qgis.core import QgsMessageLog, Qgis

from ..Map import addLayer
from .utils import (
    build_form_group_box,
    build_vbox_dialog,
    get_values,
)


def add_gee_layer_dialog(iface: gui.QgisInterface):
    """Display a dialog to add a GEE dataset to the QGIS map."""

    dialog = build_vbox_dialog(
        windowTitle="Add Google Earth Engine Image",
        widgets=[
            build_form_group_box(
                title="Dataset",
                rows=[
                    (
                        QtWidgets.QLabel(
                            text="Enter GEE Image Name (e.g., COPERNICUS/S2, USGS/SRTMGL1_003)",
                            toolTip="Provide the full Earth Engine ID.",
                        ),
                        QtWidgets.QLineEdit(objectName="imageId"),
                    )
                ],
            ),
            build_form_group_box(
                title="Visualization Parameters (JSON)",
                collapsable=True,
                collapsed=True,
                rows=[
                    (
                        QtWidgets.QLabel(
                            text="Enter JSON for visualization parameters",
                            toolTip="Example: {'min': 0, 'max': 4000, 'palette': ['006633', 'E5FFCC', '662A00']}",
                        ),
                        QtWidgets.QTextEdit(
                            objectName="vizParams",
                            placeholderText='{"min": 0, "max": 4000, "palette": ["006633", "E5FFCC", "662A00"]}',
                        ),
                    )
                ],
            ),
        ],
        accepted=lambda: _load_gee_layer(dialog),
        rejected=lambda: QgsMessageLog.logMessage(
            "User cancelled adding GEE Layer.", "GEE Plugin", level=Qgis.Info
        ),
    )

    return dialog


def _load_gee_layer(dialog: Dict[str, QtWidgets.QWidget]):
    """Fetch and add the selected Earth Engine dataset to the map with user-defined visualization parameters."""
    values = get_values(dialog)
    image_id = values["imageId"]

    if not image_id:
        message = "Image ID is required."
        QgsMessageLog.logMessage(message, "GEE Plugin", level=Qgis.Critical)
        return

    try:
        # Get asset metadata
        asset_info = ee.data.getAsset(image_id)
        asset_type = asset_info.get("type", "")

        if asset_type == "IMAGE":
            ee_object = ee.Image(image_id)
        else:
            raise ValueError(f"Unsupported asset type: {asset_type}")

        # Get visualization parameters from user as JSON
        vis_params_input = values.get("vizParams", "{}")
        if not vis_params_input:
            vis_params = {}
        else:
            try:
                vis_params = json.loads(vis_params_input.replace("'", '"'))
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format in visualization parameters.")

        # Add the dataset to QGIS map
        addLayer(ee_object, vis_params, image_id)

        success_message = (
            f"Successfully added {image_id} to the map with custom visualization."
        )
        QgsMessageLog.logMessage(success_message, "GEE Plugin", level=Qgis.Success)

    except ee.EEException as e:
        error_message = f"Earth Engine Error: {str(e)}"
        QgsMessageLog.logMessage(error_message, "GEE Plugin", level=Qgis.Critical)

    except ValueError as e:
        error_message = str(e)
        QgsMessageLog.logMessage(error_message, "GEE Plugin", level=Qgis.Critical)

    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        QgsMessageLog.logMessage(error_message, "GEE Plugin", level=Qgis.Critical)
