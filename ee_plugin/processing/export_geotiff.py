import os

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterExtent,
    QgsProcessingParameterNumber,
    QgsProcessingParameterCrs,
    QgsProcessingParameterFileDestination,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterEnum,
)

from ..logging import local_context
from .. import Map
from ..utils import ee_image_to_geotiff


class ExportGeoTIFFAlgorithm(QgsProcessingAlgorithm):
    """Export an EE Image to a GeoTIFF file."""

    OUTPUT = "OUTPUT"

    def initAlgorithm(self, config: dict) -> None:
        raster_layers = [
            layer.name()
            for layer in Map.get_iface().mapCanvas().layers()
            if layer.providerType() == "EE"
        ]
        self.raster_layers = raster_layers
        self.addParameter(
            QgsProcessingParameterEnum(
                "EE_IMAGE", "EE Image Name", options=raster_layers, optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterExtent(
                "EXTENT", "Extent", defaultValue=None, optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber("SCALE", "Scale (meters)", defaultValue=100)
        )
        self.addParameter(
            QgsProcessingParameterCrs(
                "PROJECTION", "Projection", defaultValue="EPSG:4326"
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT, "Output File", fileFilter="GeoTIFF (*.tif);;All Files (*)"
            )
        )

    def processAlgorithm(
        self,
        parameters: dict,
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict:
        # add logs to algorithm dialog
        local_context.set_feedback(feedback)
        selected_index = self.parameterAsEnum(parameters, "EE_IMAGE", context)
        ee_img = self.raster_layers[selected_index]
        rect = self.parameterAsExtent(parameters, "EXTENT", context)
        if rect is None or rect.toString() == "Null":
            raise ValueError("Bounding box extent is required for export")
        extent = [rect.xMinimum(), rect.yMinimum(), rect.xMaximum(), rect.yMaximum()]
        scale = self.parameterAsDouble(parameters, "SCALE", context)
        projection = self.parameterAsCrs(parameters, "PROJECTION", context).authid()
        out_path = self.parameterAsFile(parameters, "OUTPUT", context)

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
            raise ValueError(msg)

        ee_image = layer.dataProvider().ee_object

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

        return {self.OUTPUT: out_path}

    def name(self) -> str:
        return "export_geotiff"

    def displayName(self) -> str:
        return "Export Image to GeoTIFF"

    def group(self) -> str:
        return "Export"

    def groupId(self) -> str:
        return "export"

    def createInstance(self) -> QgsProcessingAlgorithm:
        return ExportGeoTIFFAlgorithm()

    def shortHelpString(self) -> str:
        return (
            "<h2>Export Earth Engine Image to GeoTIFF</h2>"
            "<p>This tool allows you to export an Earth Engine image to a GeoTIFF format. You must specify:</p>"
            "<ul>"
            "<li><b>Extent</b>: Coordinates defining the current map extent for the export region.</li>"
            "<li><b>Scale</b>: Resolution in meters per pixel.</li>"
            "<li><b>Projection</b>: Target projection for the exported image (e.g., EPSG:4326).</li>"
            "</ul>"
        )
