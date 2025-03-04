import logging
import json
from typing import Callable, Optional

import ee
from qgis.PyQt import QtWidgets

from ...Map import addLayer
from ..widgets import build_form_group_box, build_vbox_dialog
from ..utils import call_func_with_values
from ...utils import translate as _

logger = logging.getLogger(__name__)


def form(accepted: Optional[Callable] = None, **dialog_kwargs) -> QtWidgets.QDialog:
    """Display a dialog to add a GEE dataset to the QGIS map."""
    dialog = build_vbox_dialog(
        windowTitle=_("Add Google Earth Engine Image"),
        widgets=[
            build_form_group_box(
                title=_("Source"),
                rows=[
                    (
                        QtWidgets.QLabel(
                            text="<br />".join(
                                [
                                    _("GEE Image Name"),
                                    "e.g. <code>COPERNICUS/S2, USGS/SRTMGL1_003</code>",
                                ]
                            ),
                            toolTip="Provide the full Earth Engine ID.",
                        ),
                        QtWidgets.QLineEdit(objectName="image_id"),
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
                            objectName="viz_params",
                            placeholderText='{"min": 0, "max": 4000, "palette": ["006633", "E5FFCC", "662A00"]}',
                        ),
                    )
                ],
            ),
        ],
        **dialog_kwargs,
    )

    if accepted:
        dialog.accepted.connect(lambda: call_func_with_values(accepted, dialog))
    return dialog


def callback(image_id: str = None, viz_params: dict = None):
    """Fetch and add the selected Earth Engine dataset to the map with user-defined visualization parameters."""
    if not image_id:
        logger.error("Image ID is required.")
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
        if not viz_params:
            viz_params = {}
        else:
            try:
                viz_params = json.loads(viz_params.replace("'", '"'))
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format in visualization parameters.")

        # Add the dataset to QGIS map
        addLayer(ee_object, viz_params, image_id)

        logger.info(
            f"Successfully added {image_id} to the map with custom visualization."
        )

    except ee.EEException as e:
        logger.exception(f"Earth Engine Error: {str(e)}")

    except ValueError as e:
        logger.exception(str(e))

    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
