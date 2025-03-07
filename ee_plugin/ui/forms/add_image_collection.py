import logging
from typing import Optional, Callable
from qgis import gui
from qgis.PyQt import QtWidgets
import ee

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
                        _("Property Name"),
                        QtWidgets.QLineEdit(
                            objectName="filter_name",
                            toolTip=_(
                                "Enter the property name to filter by (e.g., CLOUD_COVER)."
                            ),
                        ),
                    ),
                    (
                        _("Operator"),
                        QtWidgets.QComboBox(
                            objectName="filter_operator",
                            editable=False,
                            toolTip=_(
                                "Choose the operator for filtering (e.g., ==, !=, <, >)."
                            ),
                        ),
                    ),
                    (
                        _("Value"),
                        QtWidgets.QLineEdit(
                            objectName="filter_value",
                            toolTip=_(
                                "Enter the value to filter by (can be numeric or string)."
                            ),
                        ),
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
        ],
        **dialog_kwargs,
    )

    # Populate operators for filtering
    operator_combo = dialog.findChild(QtWidgets.QComboBox, "filter_operator")
    operator_combo.addItems(
        [
            "Equals (==)",
            "Not Equals (!=)",
            "Less Than (<)",
            "Greater Than (>)",
            "Less Than or Equal (<=)",
            "Greater Than or Equal (>=)",
        ]
    )

    # If a callback function passed, call it with the values from the dialog
    if accepted:
        dialog.accepted.connect(
            lambda: ui_utils.call_func_with_values(accepted, dialog)
        )
    return dialog


def callback(
    image_collection_id: str,
    filter_name: str,
    filter_operator: str,
    filter_value: str,
    start_date: Optional[str],
    end_date: Optional[str],
    extent: Optional[tuple[float, float, float, float]],
):
    """
    Loads and optionally filters an ImageCollection, then adds it to the map.

    Args:
        image_collection_id (str): The Earth Engine ImageCollection ID.
        filter_name (str, optional): Name of the attribute to filter on.
        filter_operator (str, optional): Operator for filtering (==, !=, <, >, <=, >=).
        filter_value (str, optional): Value of the attribute to match.
        start_date (str, optional): Start date (YYYY-MM-DD) for filtering (must have a date property in your IC).
        end_date (str, optional): End date (YYYY-MM-DD) for filtering (must have a date property in your IC).
        extent (ee.Geometry, optional): Geometry to filter (or clip) the ImageCollection.

    Returns:
        ee.ImageCollection: The filtered ImageCollection.
    """

    ic = ee.ImageCollection(image_collection_id)

    # Apply property filter if specified
    if filter_name and filter_value:
        filter_value = (
            float(filter_value)
            if filter_value.replace(".", "", 1).isdigit()
            else filter_value
        )
        if filter_operator == "Equals (==)":
            ic = ic.filter(ee.Filter.eq(filter_name, filter_value))
        elif filter_operator == "Not Equals (!=)":
            ic = ic.filter(ee.Filter.neq(filter_name, filter_value))
        elif filter_operator == "Less Than (<)":
            ic = ic.filter(ee.Filter.lt(filter_name, filter_value))
        elif filter_operator == "Greater Than (>)":
            ic = ic.filter(ee.Filter.gt(filter_name, filter_value))
        elif filter_operator == "Less Than or Equal (<=)":
            ic = ic.filter(ee.Filter.lte(filter_name, filter_value))
        elif filter_operator == "Greater Than or Equal (>=)":
            ic = ic.filter(ee.Filter.gte(filter_name, filter_value))

    # Apply date filter if specified
    if start_date and end_date:
        ic = ic.filter(ee.Filter.date(ee.Date(start_date), ee.Date(end_date)))

    # Apply spatial filter if extent is specified
    if extent:
        ic = ic.filterBounds(ee.Geometry.Rectangle(extent))

    # Create a median composite for visualization
    composite = ic.median()

    # Add to map
    layer_name = f"IC: {image_collection_id}"
    Map.addLayer(composite, {}, layer_name)

    return ic
