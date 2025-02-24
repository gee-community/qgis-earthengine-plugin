from typing import Optional, Callable
from qgis import gui
from qgis.PyQt import QtWidgets
import ee

from ..utils import (
    call_func_with_values,
)
from .. import widgets
from ... import Map, utils
from ...utils import translate as _


def form(
    iface: gui.QgisInterface,
    accepted: Optional[Callable] = None,
    **dialog_kwargs,
) -> QtWidgets.QDialog:
    """Add a GEE Feature Collection to the map."""
    dialog = widgets.build_vbox_dialog(
        windowTitle=_("Add Feature Collection"),
        widgets=[
            widgets.build_form_group_box(
                title=_("Source"),
                rows=[
                    (
                        QtWidgets.QLabel(
                            toolTip=_("The Earth Engine Feature Collection ID."),
                            text="<br />".join(
                                [
                                    _("Feature Collection ID"),
                                    "e.g. <code>USGS/WBD/2017/HUC06</code>",
                                ]
                            ),
                        ),
                        QtWidgets.QLineEdit(
                            objectName="feature_collection_id",
                        ),
                    ),
                    (
                        QtWidgets.QLabel(
                            _("Retain as a vector layer"),
                            toolTip=_(
                                "Store as a vector layer rather than WMS Raster layer."
                            ),
                            whatsThis=_(
                                "Attempt to retain the layer as a vector layer, running "
                                "the risk of encountering Earth Engine API limitations if "
                                "the layer is large. Otherwise, the layer will be added as "
                                "a WMS raster layer."
                            ),
                        ),
                        QtWidgets.QCheckBox(
                            objectName="as_vector",
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
                        _("Name"),
                        QtWidgets.QLineEdit(objectName="filter_name"),
                    ),
                    (
                        _("Value"),
                        QtWidgets.QLineEdit(objectName="filter_value"),
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
                        widgets.DefaultNullQgsDateEdit(objectName="start_date"),
                    ),
                    (
                        "End",
                        widgets.DefaultNullQgsDateEdit(objectName="end_date"),
                    ),
                ],
            ),
            gui.QgsExtentGroupBox(
                objectName="extent",
                title=_("Filter by Coordinates"),
                collapsed=True,
            ),
            widgets.build_form_group_box(
                title=_("Visualization"),
                collapsable=True,
                collapsed=True,
                rows=[
                    (
                        _("Color"),
                        gui.QgsColorButton(objectName="viz_color_hex"),
                    ),
                ],
            ),
        ],
        parent=iface.mainWindow(),
        **dialog_kwargs,
    )

    # If a callback function passed, call it with the values from the dialog
    if accepted:
        dialog.accepted.connect(lambda: call_func_with_values(accepted, dialog))
    return dialog


def callback(
    feature_collection_id: str,
    filter_name: str,
    filter_value: str,
    start_date: Optional[str],
    end_date: Optional[str],
    extent: Optional[tuple[float, float, float, float]],
    viz_color_hex: str,
    as_vector: bool,
):
    """
    Loads and optionally filters a FeatureCollection, then adds it to the map.

    Args:
        feature_collection_id (str): The Earth Engine FeatureCollection ID.
        filter_name (str, optional): Name of the attribute to filter on.
        filter_value (str, optional): Value of the attribute to match.
        start_date (str, optional): Start date (YYYY-MM-DD) for filtering (must have a date property in your FC).
        end_date (str, optional): End date (YYYY-MM-DD) for filtering (must have a date property in your FC).
        extent (ee.Geometry, optional): Geometry to filter (or clip) the FeatureCollection.
        viz_color_hex (str, optional): Hex color code for styling the features.

    Returns:
        ee.FeatureCollection: The filtered FeatureCollection.
    """

    fc = ee.FeatureCollection(feature_collection_id)

    if filter_name and filter_value:
        fc = fc.filter(ee.Filter.eq(filter_name, filter_value))

    if start_date and end_date:
        fc = fc.filter(ee.Filter.date(ee.Date(start_date), ee.Date(end_date)))

    if extent:
        fc = fc.filterBounds(ee.Geometry.Rectangle(extent))

    # 6. Add to map
    layer_name = f"FC: {feature_collection_id}"
    if as_vector:
        try:
            utils.add_ee_vector_layer(fc, layer_name)
        except ee.ee_exception.EEException as e:
            Map.get_iface().messageBar().pushMessage(
                "Error",
                f"Failed to load the Feature Collection: {e}",
                level=gui.Qgis.Critical,
            )
    else:
        Map.addLayer(fc, {"palette": viz_color_hex}, layer_name)
    return fc
