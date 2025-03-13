import json
import logging
from typing import Optional, Callable

import ee
from qgis import gui
from qgis.PyQt import QtWidgets

from .. import widgets, utils as ui_utils
from ... import Map
from ...utils import translate as _

logger = logging.getLogger(__name__)


def form(
    accepted: Optional[Callable] = None,
    **dialog_kwargs,
) -> QtWidgets.QDialog:
    """Add a GEE Image Collection to the map."""
    dialog = widgets.build_vbox_dialog(
        windowTitle=_("Add Image Collection"),
        widgets=[
            widgets.build_form_group_box(
                title=_("Source"),
                rows=[
                    (
                        QtWidgets.QLabel(
                            toolTip=_("The Earth Engine Image Collection ID."),
                            text="<br />".join(
                                [
                                    _("Image Collection ID"),
                                    "e.g. <code>LANDSAT/LC09/C02/T1_L2</code>",
                                ]
                            ),
                        ),
                        QtWidgets.QLineEdit(
                            objectName="image_collection_id",
                            toolTip=_(
                                "Enter the ID of the Earth Engine Image Collection (e.g., LANDSAT/LC09/C02/T1_L2)."
                            ),
                        ),
                    ),
                ],
            ),
            widgets.build_form_group_box(
                title=_("Filter by Properties"),
                collapsable=True,
                collapsed=True,
                rows=[
                    (
                        QtWidgets.QLabel(
                            text=_("Filters:"),
                            toolTip=_("Add multiple filters by clicking 'Add Filter'."),
                        ),
                        widgets.create_filter_widget(),  # Updated: Ensure object name is set
                    ),
                ],
            ),
            widgets.build_form_group_box(
                title=_("Filter by Dates"),
                collapsable=True,
                collapsed=True,
                rows=[
                    (
                        "Start",
                        widgets.DefaultNullQgsDateEdit(
                            objectName="start_date",
                            toolTip=_(
                                "Select the start date for filtering the image collection."
                            ),
                        ),
                    ),
                    (
                        "End",
                        widgets.DefaultNullQgsDateEdit(
                            objectName="end_date",
                            toolTip=_(
                                "Select the end date for filtering the image collection."
                            ),
                        ),
                    ),
                ],
            ),
            gui.QgsExtentGroupBox(
                objectName="extent",
                title=_("Filter by Coordinates"),
                collapsed=True,
                toolTip=_(
                    "Specify the geographic extent to filter the image collection."
                ),
            ),
            widgets.build_form_group_box(
                title="Visualization Parameters (JSON)",
                collapsable=True,
                collapsed=True,
                rows=[
                    (
                        QtWidgets.QLabel(
                            text="Enter JSON for visualization parameters",
                            toolTip="Example: {'bands':['SR_B4','SR_B3','SR_B2'],'min':0,'max':30000,'gamma':1.3}",
                        ),
                        QtWidgets.QTextEdit(
                            objectName="viz_params",
                            placeholderText="{'bands':['SR_B4','SR_B3','SR_B2'],'min':0,'max':30000,'gamma':1.3}",
                        ),
                    )
                ],
            ),
        ],
        **dialog_kwargs,
    )

    # If a callback function is passed, call it with the values from the dialog
    if accepted:
        dialog.accepted.connect(
            lambda: ui_utils.call_func_with_values(accepted, dialog)
        )
    return dialog


def callback(
    image_collection_id: str,
    start_date: Optional[str],
    end_date: Optional[str],
    extent: Optional[tuple[float, float, float, float]],
    filters: Optional[list] = None,  # New parameter for multiple filters
    viz_params: Optional[dict] = None,
):
    """
    Loads and optionally filters an ImageCollection, then adds it to the map.

    Args:
        image_collection_id (str): The Earth Engine ImageCollection ID.
        start_date (str, optional): Start date (YYYY-MM-DD) for filtering.
        end_date (str, optional): End date (YYYY-MM-DD) for filtering.
        extent (ee.Geometry, optional): Geometry to filter (or clip) the ImageCollection.
        filters (list, optional): List of property filters to apply.

    Returns:
        ee.ImageCollection: The filtered ImageCollection.
    """
    ic = ee.ImageCollection(image_collection_id)

    if filters:
        # Define a dictionary to map operators to corresponding ee.Filter functions
        filter_functions = {
            "Equals (==)": ee.Filter.eq,
            "Not Equals (!=)": ee.Filter.neq,
            "Less Than (<)": ee.Filter.lt,
            "Greater Than (>)": ee.Filter.gt,
            "Less Than or Equal (<=)": ee.Filter.lte,
            "Greater Than or Equal (>=)": ee.Filter.gte,
        }

        for f in filters:
            filter_name, filter_operator, filter_value = f
            # Convert filter_value to float if it's a valid number, otherwise keep as string
            filter_value = (
                float(filter_value)
                if filter_value.replace(".", "", 1).isdigit()
                else filter_value
            )
            filter_func = filter_functions.get(filter_operator)
            if filter_func:
                ic = ic.filter(filter_func(filter_name, filter_value))
            else:
                # Log an error if the filter operator is invalid
                # somewhat hot take:
                # do not add ImageCollection to the map
                # if the filter operator is invalid, could lead to unexpected results for the user
                logger.error(f"Invalid filter operator: {filter}.")
                return

    # Apply date filter if specified
    if start_date and end_date:
        ic = ic.filter(ee.Filter.date(ee.Date(start_date), ee.Date(end_date)))

    # Apply spatial filter if extent is specified
    if extent:
        ic = ic.filterBounds(ee.Geometry.Rectangle(extent))

    # Get visualization parameters from user as JSON
    if not viz_params:
        viz_params = {}
    elif isinstance(viz_params, str):  # Ensure it's a string before replacing quotes
        try:
            viz_params = json.loads(viz_params.replace("'", '"'))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format in visualization parameters: {str(e)}")
            raise json.JSONDecodeError(
                "Invalid JSON format in visualization parameters",
                viz_params,  # The problematic string
                0,  # Position of error (use actual error position if available)
            )

    # Add to map
    layer_name = f"IC: {image_collection_id}"
    Map.addLayer(ic.mosaic(), viz_params, layer_name)
    logger.info(
        f"Added ImageCollection {image_collection_id} to the map as {layer_name}"
    )

    return ic
