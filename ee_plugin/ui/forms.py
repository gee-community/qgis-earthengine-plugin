from typing import Optional
from qgis import gui
from qgis.PyQt import QtWidgets, QtCore
import ee

from .utils import (
    build_form_group_box,
    build_vbox_dialog,
    get_values,
)

from .. import Map, utils


def DefaultNullQgsDateEdit(
    *, date: Optional[QtCore.QDate] = None, **kwargs
) -> gui.QgsDateEdit:
    """Build a QgsDateEdit widget, with null default capability."""
    d = gui.QgsDateEdit(**kwargs)
    # It would be great to remove this helper and just use the built-in QgsDateEdit class
    # but at this time it's not clear how to make a DateEdit widget that initializes with
    # a null value. This is a workaround.
    if date is None:
        d.clear()
    else:
        d.setDate(date)
    return d


def add_feature_collection_form(
    iface: gui.QgisInterface, **dialog_kwargs
) -> QtWidgets.QDialog:
    """Add a GEE Feature Collection to the map."""
    dialog = build_vbox_dialog(
        windowTitle="Add Feature Collection",
        widgets=[
            build_form_group_box(
                title="Source",
                rows=[
                    (
                        QtWidgets.QLabel(
                            text="<br />".join(
                                [
                                    "Add GEE Feature Collection to Map",
                                    "e.g. <code>USGS/WBD/2017/HUC06</code>",
                                ]
                            ),
                            toolTip="This is a tooltip!",
                            whatsThis='This is "WhatsThis"! <a href="http://google.com">Link</a>',
                        ),
                        QtWidgets.QLineEdit(objectName="feature_collection_id"),
                    ),
                    (
                        "Retain as a vector layer",
                        QtWidgets.QCheckBox(objectName="use_util"),
                    ),
                ],
            ),
            build_form_group_box(
                title="Filter by Properties",
                collapsable=True,
                collapsed=True,
                rows=[
                    (
                        "Name",
                        QtWidgets.QLineEdit(objectName="filter_name"),
                    ),
                    (
                        "Value",
                        QtWidgets.QLineEdit(objectName="filter_value"),
                    ),
                ],
            ),
            build_form_group_box(
                title="Filter by Dates",
                collapsable=True,
                collapsed=True,
                rows=[
                    (
                        "Start",
                        DefaultNullQgsDateEdit(objectName="start_date"),
                    ),
                    (
                        "End",
                        DefaultNullQgsDateEdit(objectName="end_date"),
                    ),
                ],
            ),
            gui.QgsExtentGroupBox(
                objectName="extent",
                title="Filter by Coordinates",
                collapsed=True,
            ),
            build_form_group_box(
                title="Visualization",
                collapsable=True,
                collapsed=True,
                rows=[
                    ("Color", gui.QgsColorButton(objectName="viz_color_hex")),
                ],
            ),
        ],
        parent=iface.mainWindow(),
        **dialog_kwargs,
    )

    dialog.accepted.connect(lambda: add_feature_collection(**get_values(dialog)))
    return dialog


def add_feature_collection(
    feature_collection_id: str,
    filter_name: str,
    filter_value: str,
    start_date: Optional[str],
    end_date: Optional[str],
    extent: Optional[tuple[float, float, float, float]],
    viz_color_hex: str,
    use_util: bool,
    **kwargs,
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
    if use_util:
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
