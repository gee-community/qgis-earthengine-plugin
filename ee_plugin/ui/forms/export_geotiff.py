import os
import logging
from typing import Optional, Callable

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

    ee_img_msg = _("Select an Earth Engine image to export.")
    ee_image_dropdown = widgets.DropdownWidget(
        object_name="ee_img", options=raster_layers, toolTip=ee_img_msg
    )

    extent_msg = _(
        "The bounding box to filter the image by coordinates in the selected projection units."
    )
    extent_box = gui.QgsExtentGroupBox(
        objectName="extent",
        title=_("Filter by Coordinates"),
        collapsed=False,
        toolTip=extent_msg,
    )
    extent_box.setCheckable(False)
    extent_box.setEnabled(True)

    scale_msg = _("The scale of the exported image in meters per pixel.")
    scale_spinbox = QtWidgets.QDoubleSpinBox(
        objectName="scale", minimum=1, maximum=10000, toolTip=scale_msg
    )

    projection_msg = _("The projection of the exported image (EPSG code).")
    projection_dropdown = gui.QgsProjectionSelectionWidget(
        objectName="projection", toolTip=projection_msg
    )
    projection_dropdown.setCrs(QgsCoordinateReferenceSystem.fromEpsgId(4326))

    output_file_msg = _("The file path to save the exported GeoTIFF.")
    output_file_selector = widgets.FileSelectionWidget(
        object_name="out_path",
        caption=_("Select Output File"),
        filter="GeoTIFF (*.tif);;All Files (*)",
        save_mode=True,
        toolTip=output_file_msg,
    )

    dialog = widgets.build_vbox_dialog(
        windowTitle=_("Export GeoTIFF"),
        widgets=[
            widgets.build_form_group_box(
                title=_("Source"),
                rows=[
                    (
                        QtWidgets.QLabel(_("Select EE Image"), toolTip=ee_img_msg),
                        ee_image_dropdown,
                    )
                ],
            ),
            extent_box,
            widgets.build_form_group_box(
                title=_("Settings"),
                rows=[
                    (
                        QtWidgets.QLabel(_("Scale (meters)"), toolTip=scale_msg),
                        scale_spinbox,
                    ),
                    (
                        QtWidgets.QLabel(_("Projection"), toolTip=projection_msg),
                        projection_dropdown,
                    ),
                    (
                        QtWidgets.QLabel(_("Output File"), toolTip=output_file_msg),
                        output_file_selector,
                    ),
                ],
            ),
        ],
        **dialog_kwargs,
    )

    # Try to populate extent from current map canvas
    try:
        canvas = Map.get_iface().mapCanvas()
        canvas_extent = canvas.extent()
        canvas_crs = canvas.mapSettings().destinationCrs()
        extent_box.setOriginalExtent(canvas_extent, canvas_crs)
        extent_box.setCRS(canvas_crs)
        logger.debug("Set extent from current map canvas")
    except Exception as e:
        logger.warning(f"Could not set extent from current canvas: {e}")

    if accepted:
        dialog.accepted.connect(
            lambda: ui_utils.call_func_with_values(accepted, dialog)
        )

    return dialog


def callback(
    ee_img: str,
    extent: Optional[tuple[float, float, float, float]],
    scale: float,
    projection: str,
    out_path: str,
):
    """Export an EE Image to a GeoTIFF file."""
    if extent is None:
        logger.exception("Bounding box extent is required for export")
        raise ValueError("Bounding box extent is required for export")

    layer = next(
        (
            layer
            for layer in Map.get_iface().mapCanvas().layers()
            if layer.name() == ee_img and layer.providerType() == "EE"
        ),
        None,
    )

    if not layer:
        msg = f"Layer {ee_img} not found"
        logger.error(msg)
        raise ValueError(msg)

    ee_image = layer.dataProvider().ee_object

    try:
        tile_dir = os.path.dirname(out_path)
        if tile_dir == "":
            tile_dir = os.getcwd()
        base_name = os.path.splitext(os.path.basename(out_path))[0]

        ee_image_to_geotiff(
            ee_image=ee_image,
            extent=extent,
            scale=scale,
            projection=projection,
            out_dir=tile_dir,
            base_name=base_name,
            merge_output=out_path,
        )
        logger.info(f"GeoTIFF exported to {out_path}")

    except Exception as e:
        logger.exception(f"Error exporting GeoTIFF: {e}")
