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
    iface: gui.QgisInterface, _debug=True, **kwargs
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
                        "Use <pre>add_or_update_ee_vector_layer</pre>",
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
        **kwargs,
    )

    if _debug:
        dialog.accepted.connect(
            lambda: iface.messageBar().pushMessage(f"Accepted {get_values(dialog)=}")
        )

    dialog.accepted.connect(lambda: add_feature_collection(**get_values(dialog)))

    return dialog


def add_feature_collection(
    feature_collection_id: str,
    filter_name: str,
    filter_value: str,
    start_date: str,
    end_date: str,
    mYMaxLineEdit: str,
    mYMinLineEdit: str,
    mXMaxLineEdit: str,
    mXMinLineEdit: str,
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

    # if start_date and end_date:
    #     fc = fc.filter(
    #         ee.Filter.date(ee.Date(start_date), ee.Date(end_date))
    #         # If your features store date in a property named "date", you might need:
    #         # ee.Filter.calendarRange(
    #         #     start_date, end_date, 'year' (or 'day', etc.) if using calendarRange
    #     )

    extent_src = [mXMinLineEdit, mYMinLineEdit, mXMaxLineEdit, mYMaxLineEdit]
    if all(extent_src):
        extent = ee.Geometry.Rectangle([float(val) for val in extent_src])

        # Alternatively, if you want to clip features to the extent rather than just filter:
        fc = fc.filterBounds(extent)

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
        Map.addLayer(
            fc,
            {
                # "color": viz_color_hex,
                # If you'd like transparency or a custom fill color, you can add:
                # "fillColor": viz_color_hex,
                # "opacity": 0.6,
                "palette": viz_color_hex,
            },
            layer_name,
        )
    return fc
