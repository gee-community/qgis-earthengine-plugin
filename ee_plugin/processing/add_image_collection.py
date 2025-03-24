from typing import List

import ee
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterString,
    QgsProcessingParameterEnum,
    QgsProcessingParameterDateTime,
    QgsProcessingParameterNumber,
    QgsProcessingOutputRasterLayer,
    QgsProcessingOutputString,
    QgsProcessingParameterExtent,
)

from .. import Map


filter_functions = {
    "==": {"operator": ee.Filter.eq, "symbol": "=="},
    "!=": {"operator": ee.Filter.neq, "symbol": "!="},
    "<": {"operator": ee.Filter.lt, "symbol": "<"},
    ">": {"operator": ee.Filter.gt, "symbol": ">"},
    "<=": {"operator": ee.Filter.lte, "symbol": "<="},
    ">=": {"operator": ee.Filter.gte, "symbol": ">="},
}


class AddImageCollectionAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to add an Image Collection to the map from GEE.
    """

    def name(self):
        return "add_image_collection"

    def displayName(self):
        return "Add Image Collection"

    def group(self) -> str:
        return "Add Layer"

    def groupId(self) -> str:
        return "gee"

    def shortHelpString(self):
        return """
        <html>
        <b>Add Image Collection</b><br>
        This algorithm adds an Earth Engine Image Collection to the map with the specified compositing method and visualization parameters.<br>
        You can filter the collection by properties, dates, or geographic extent.<br>

        <h3>Parameters:</h3>
        <ul>
            <li><b>Image Collection ID:</b> The Earth Engine Image Collection ID to add to the map.</li>
            <li><b>Filters:</b> The filter type to apply to the Image Collection. Example: "cloud_coverage:&lt;:10;sun_elevation:&gt;:0" for non-cloudy daytime Landsat images.</li>
            <li><b>Start date for filtering:</b> The start date for filtering the Image Collection.</li>
            <li><b>End date for filtering:</b> The end date for filtering the Image Collection.</li>
            <li><b>Compositing Method:</b> The compositing method to use for the Image Collection.</li>
            <li><b>Percentile Value:</b> The percentile value to use for the 'Percentile' compositing method if selected.</li>
        </ul>

        <b>Earth Engine Data Catalog:</b><br>
            <a href='https://developers.google.com/earth-engine/datasets'>https://developers.google.com/earth-engine/datasets</a>
        </html>
        """

    def initAlgorithm(self, config):
        # Define parameters
        self.addParameter(
            QgsProcessingParameterString(
                "image_collection_id", "Earth Engine Image Collection ID"
            )
        )
        self.addParameter(
            QgsProcessingParameterExtent("extent", "Extent", optional=True)
        )
        self.addParameter(
            QgsProcessingParameterString(
                "filters",
                "Filter Expression",
                "Enter filters as property_0:operator_0:value_0;property_1:operator_1:value_1",
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterDateTime(
                "start_date", "Start date for filtering", optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterDateTime(
                "end_date", "End date for filtering", optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                "compositing_method",
                "Compositing Method",
                options=["Mosaic", "Mean", "Max", "Min", "Median", "Percentile"],
                optional=False,
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "percentile_value", "Percentile Value", optional=True
            )
        )

        self.addOutput(QgsProcessingOutputRasterLayer("OUTPUT", "EE Image"))
        self.addOutput(QgsProcessingOutputString("LAYER_NAME", "Layer Name"))

    def createInstance(self):
        return AddImageCollectionAlgorithm()

    def _get_filters(self, filters: str) -> List[str]:
        filters = filters.split(";")
        parsed_filters = []
        for f in filters:
            f = f.split(":")
            if len(f) == 3 and f[1] in filter_functions:
                parsed_filters.append(f)
            else:
                raise ValueError(f"Invalid filter format: {f}")

        return parsed_filters

    def processAlgorithm(self, parameters, context, feedback):
        image_collection_id = parameters["image_collection_id"]
        filters = parameters["filters"]
        start_date = parameters["start_date"]
        end_date = parameters["end_date"]
        extent = parameters["extent"]  # This is the extent parameter as a string
        compositing_method = parameters["compositing_method"]
        percentile_value = parameters["percentile_value"]

        # Initialize Earth Engine ImageCollection
        ic = ee.ImageCollection(image_collection_id)

        # Apply date filter if provided
        if start_date and end_date:
            start_date_str = start_date.toString("yyyy-MM-dd")
            end_date_str = end_date.toString("yyyy-MM-dd")
            ic = ic.filter(
                ee.Filter.date(ee.Date(start_date_str), ee.Date(end_date_str))
            )

        # If extent is provided, convert it to a QgsRectangle and then to ee.Geometry
        if extent:
            # Extract coordinates from the string (example: '-125.414732328,-120.326515344,48.801746245,52.242572656 [EPSG:4326]')
            extent = extent.split(" ")[0]  # Take just the coordinates part
            coords = extent.split(",")  # Split into individual coordinates
            min_lon, max_lon, min_lat, max_lat = map(float, coords)  # Convert to float

            # Create the Earth Engine geometry
            ee_extent = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])
            ic = ic.filterBounds(ee_extent)

        # Apply the filters if provided
        filters = self._get_filters(filters)
        for filter in filters:
            filter_property, filter_operator, filter_value = filter
            filter_func = filter_functions.get(f"{filter_operator} ({filter_property})")
            if filter_func:
                ic = ic.filter(filter_func["operator"](filter_property, filter_value))

        # Apply compositing logic
        compositing_dict = {
            "Mean": ic.mean(),
            "Max": ic.max(),
            "Min": ic.min(),
            "Median": ic.median(),
            "Percentile": ic.reduce(ee.Reducer.percentile([percentile_value])),
        }

        ic = compositing_dict.get(compositing_method, ic.mosaic())

        # Add the image collection to the map
        layer = Map.addLayer(
            ic, {}, f"IC: {image_collection_id} ({compositing_method})"
        )

        return {"OUTPUT": layer, "LAYER_NAME": layer.name()}
