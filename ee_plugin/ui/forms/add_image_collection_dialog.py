import logging
from typing import Optional, Callable
from qgis import gui
from qgis.PyQt import QtWidgets

from .. import widgets, utils as ui_utils
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
