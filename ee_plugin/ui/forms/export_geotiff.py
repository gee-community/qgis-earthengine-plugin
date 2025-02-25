from typing import Optional, Callable
from qgis import gui
from qgis.PyQt import QtWidgets
import ee
import xarray as xr

from .. import widgets, utils as ui_utils
from ... import Map
from ...utils import translate as _

# Define a list of common EPSG projections
PROJECTIONS = [
    ("EPSG:4326 (WGS 84)", "EPSG:4326"),
    ("EPSG:3857 (Web Mercator)", "EPSG:3857"),
    ("EPSG:32633 (UTM Zone 33N)", "EPSG:32633"),
]


def form(
    accepted: Optional[Callable] = None,
    **dialog_kwargs,
) -> QtWidgets.QDialog:
    """Export an EE Image to a GeoTIFF."""

    # Get layers that are of type 'EarthEngineRasterDataProvider'
    raster_layers = [
        layer.name()
        for layer in Map.get_iface().mapCanvas().layers()
        if layer.providerType() == "EE"
    ]

    dialog = widgets.build_vbox_dialog(
        windowTitle=_("Export GeoTIFF"),
        widgets=[
            widgets.build_form_group_box(
                title=_("Source"),
                rows=[
                    (
                        QtWidgets.QLabel(_("Select EE Image")),
                        widgets.DropdownWidget("ee_img", raster_layers),
                    ),
                ],
            ),
            gui.QgsExtentGroupBox(
                objectName="extent",
                title=_("Filter by Coordinates"),
                collapsed=True,
            ),
            widgets.build_form_group_box(
                title=_("Export Settings"),
                rows=[
                    (
                        QtWidgets.QLabel(_("Scale (meters per pixel)")),
                        QtWidgets.QSpinBox(
                            objectName="scale", minimum=10, maximum=10000, value=1000
                        ),
                    ),
                    (
                        QtWidgets.QLabel(_("Projection")),
                        QtWidgets.QComboBox(
                            objectName="projection",
                        ).addItems([name for name, _ in PROJECTIONS]),
                    ),
                    (
                        QtWidgets.QLabel(_("Output File")),
                        widgets.FileSelectionWidget(
                            caption=_("Select Output File"),
                            filter="GeoTIFF (*.tif);;All Files (*)",
                            save_mode=True,
                        ),
                    ),
                ],
            ),
        ],
        **dialog_kwargs,
    )

    # If a callback function is passed, connect it
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
    """
    Export an EE Image to a GeoTIFF file.

    Args:
        ee_img (str): The name of the EE Image layer.
        extent (tuple, optional): Bounding box to export (xmin, ymin, xmax, ymax).
        scale (int): Scale in meters per pixel.
        projection (str): EPSG projection code.
        out_path (str): Output file path.

    Returns:
        None
    """

    # Get the selected EE Image from the map
    layer = next(
        (
            layer
            for layer in Map.get_iface().mapCanvas().layers()
            if layer.name() == ee_img and layer.providerType() == "EE"
        ),
        None,
    )

    if not layer:
        Map.get_iface().messageBar().pushMessage(
            "Error", "Selected layer not found.", level=gui.Qgis.Critical
        )
        return

    # Convert layer to EE Image
    ee_image = ee.Image(layer.source())

    # If no region is specified, use the full bounds
    if extent:
        region = ee.Geometry.Rectangle(extent)
    else:
        region = ee_image.geometry().bounds()

    # Export EE Image to GeoTIFF
    try:
        ix = xr.open_dataset(
            ee.ImageCollection(ee_image),
            engine="ee",
            scale=scale,
            projection=projection,
            geometry=region,
        )

        out_ds = (
            ix.isel(time=0)
            .rio.write_crs(ix.attrs["crs"])
            .rename({"lon": "x", "lat": "y"})
        )

        out_ds.rio.to_raster(out_path, windowed=True)

        Map.get_iface().messageBar().pushMessage(
            "Success", "Export complete.", level=gui.Qgis.Success
        )

    except Exception as e:
        Map.get_iface().messageBar().pushMessage(
            "Error", str(e), level=gui.Qgis.Critical
        )
