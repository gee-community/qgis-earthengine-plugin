import logging
from typing import Optional, Callable

import ee
from qgis import gui
from qgis.core import QgsCoordinateReferenceSystem
from qgis.PyQt import QtWidgets

from .. import widgets, utils as ui_utils
from ... import Map
from ...utils import translate as _, ee_image_to_geotiff


logger = logging.getLogger(__name__)


def form(accepted: Optional[Callable] = None, **dialog_kwargs) -> QtWidgets.QDialog:
    """Export an EE Image to a GeoTIFF."""
    raster_layers = [
        layer.name()
        for layer in Map.get_iface().mapCanvas().layers()
        if layer.providerType() == "EE"
    ]

    ee_image_dropdown = widgets.DropdownWidget(
        object_name="ee_img", options=raster_layers
    )

    extent_box = gui.QgsExtentGroupBox(
        objectName="extent",
        title=_("Filter by Coordinates"),
        collapsed=True,
    )

    scale_msg = _("The scale of the exported image in projection units per pixel.")
    scale_spinbox = QtWidgets.QDoubleSpinBox(
        objectName="scale", minimum=10, maximum=10000, value=1000, toolTip=scale_msg
    )

    projection_dropdown = gui.QgsProjectionSelectionWidget(objectName="projection")
    projection_dropdown.setCrs(QgsCoordinateReferenceSystem.fromEpsgId(4326))

    output_file_selector = widgets.FileSelectionWidget(
        object_name="out_path",
        caption=_("Select Output File"),
        filter="GeoTIFF (*.tif);;All Files (*)",
        save_mode=True,
    )

    dialog = widgets.build_vbox_dialog(
        windowTitle=_("Export GeoTIFF"),
        widgets=[
            widgets.build_form_group_box(
                title=_("Source"),
                rows=[
                    (QtWidgets.QLabel(_("Select EE Image")), ee_image_dropdown),
                ],
            ),
            extent_box,
            widgets.build_form_group_box(
                title=_("Settings"),
                rows=[
                    (QtWidgets.QLabel(_("Scale"), toolTip=scale_msg), scale_spinbox),
                    (QtWidgets.QLabel(_("Projection")), projection_dropdown),
                    (QtWidgets.QLabel(_("Output File")), output_file_selector),
                ],
            ),
        ],
        **dialog_kwargs,
    )

    if accepted:
        dialog.accepted.connect(
            lambda: ui_utils.call_func_with_values(accepted, dialog)
        )

    return dialog


def callback(
    ee_img: str,
    extent: Optional[tuple[float, float, float, float]],
    scale: int,
    projection: str,
    out_path: str,
):
    """Export an EE Image to a GeoTIFF file."""
    # Error handling for unsupported EPSG codes
    try:
        ee.Projection(projection)
    except ee.EEException:
        logger.exception(f"Unsupported EPSG code: {projection}")
        return

    layer = next(
        (
            layer
            for layer in Map.get_iface().mapCanvas().layers()
            if layer.name() == ee_img and layer.providerType() == "EE"
        ),
        None,
    )

    if not layer:
        logger.exception(f"Layer {ee_img} not found")
        return

    ee_image = layer.dataProvider().ee_object

    if extent:
        region = ee.Geometry.Rectangle(extent, proj=projection, geodesic=False)
    else:
        region = ee_image.geometry().bounds()

    try:
        ee_image_to_geotiff(ee_image, out_path, scale, projection, region)
        logger.info(f"GeoTIFF exported to {out_path}")

    except Exception as e:
        logger.exception(f"Error exporting GeoTIFF: {e}")
