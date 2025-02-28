from typing import Optional, Callable

import ee
import xarray as xr
from qgis import gui
from qgis.core import QgsMessageLog, Qgis
from qgis.PyQt import QtWidgets

from .. import widgets, utils as ui_utils
from ... import Map
from ...utils import translate as _

# TODO: don't use hardcoded values
PROJECTIONS = [
    "EPSG:4326",
    "EPSG:3857",
    "EPSG:32633",
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

    # Define widgets at the top level
    ee_image_dropdown = widgets.DropdownWidget(
        object_name="ee_img", options=raster_layers
    )

    extent_box = gui.QgsExtentGroupBox(
        objectName="extent",
        title=_("Filter by Coordinates"),
        collapsed=True,
    )

    scale_spinbox = QtWidgets.QSpinBox(
        objectName="scale", minimum=10, maximum=10000, value=1000
    )

    projection_dropdown = widgets.DropdownWidget(
        object_name="projection", options=PROJECTIONS
    )

    output_file_selector = widgets.FileSelectionWidget(
        object_name="out_path",
        caption=_("Select Output File"),
        filter="GeoTIFF (*.tif);;All Files (*)",
        save_mode=True,
    )

    # Build the dialog using top-level widgets
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
                    (QtWidgets.QLabel(_("Scale (meters per pixel)")), scale_spinbox),
                    (QtWidgets.QLabel(_("Projection")), projection_dropdown),
                    (QtWidgets.QLabel(_("Output File")), output_file_selector),
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
        QgsMessageLog.logMessage(
            f"Layer {ee_img} not found", "GEE Plugin", level=Qgis.Critical
        )
        return

    ee_image = layer.dataProvider().ee_object

    # If no region is specified, use the full bounds
    if extent:
        # geodesic=False is important for non-WGS84 projections
        region = ee.Geometry.Rectangle(extent, proj=projection, geodesic=False)
    else:
        region = ee_image.geometry().bounds()

    # Export EE Image to GeoTIFF
    try:
        ix = xr.open_dataset(
            ee_image,
            engine="ee",
            scale=scale,
            crs=projection,
            geometry=region,
        )

        # Remove time dimension if it exists
        if "time" in ix.dims:
            ix = ix.isel(time=0, drop=True)

        # Identify first data variable (e.g., "elevation") and extract it
        data_var = list(ix.data_vars.keys())[0]  # Get the first variable name
        ix = ix[data_var]  # Extract the variable as a DataArray

        # Ensure spatial dimensions are set correctly
        try:
            ix = ix.rename({"lon": "x", "lat": "y"})
        except ValueError:
            # dimensions are capitalized
            # Non WGS84 projections already have x, y dimensions
            ix = ix.rename({"X": "x", "Y": "y"})

        ix.rio.set_spatial_dims(x_dim="x", y_dim="y", inplace=True)
        ix = ix.transpose("y", "x")
        ix = ix.rio.write_crs(projection, inplace=True)

        # Export GeoTIFF
        ix.rio.to_raster(out_path, windowed=True, projection=projection)

        QgsMessageLog.logMessage(
            f"Successfully exported {ee_img}", "GEE Plugin", level=Qgis.Success
        )

    except Exception as e:
        QgsMessageLog.logMessage(
            f"Error exporting {ee_img}: {str(e)}", "GEE Plugin", level=Qgis.Critical
        )
        return
