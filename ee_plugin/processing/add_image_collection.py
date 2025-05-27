import json
import logging
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
    QgsRectangle,
)
from qgis.PyQt.QtCore import QTimer, QDate
from qgis.PyQt.QtWidgets import (
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QSlider,
    QHBoxLayout,
    QWidget,
    QColorDialog,
)
from qgis import gui

from .custom_algorithm_dialog import BaseAlgorithmDialog
from .. import Map
from ..ui.widgets import VisualizationParamsWidget, FilterWidget
from ..utils import (
    translate as _,
    get_ee_properties,
    get_available_bands,
    filter_functions,
)
from ..ui.utils import serialize_color_ramp

logger = logging.getLogger(__name__)


class AddImageCollectionAlgorithmDialog(BaseAlgorithmDialog):
    def __init__(self, algorithm: QgsProcessingAlgorithm, parent: QWidget = None):
        self.image_properties = []
        super().__init__(algorithm, parent=parent, title="Add Image Collection")
        self._update_timer = QTimer(
            self, singleShot=True, timeout=self._on_image_collection_id_ready
        )

    def update_image_properties(self):
        asset_id = self.image_collection_id.text().strip()
        if not asset_id:
            return
        props = get_ee_properties(asset_id, silent=True)
        if props:
            self.image_properties = props
            self._refresh_property_dropdowns()

    def _on_image_collection_id_changed(self):
        self._update_timer.start(500)

    def _on_image_collection_id_ready(self):
        self.update_image_properties()
        self.update_band_dropdowns()

    def _refresh_property_dropdowns(self):
        self.filter_widget.set_property_list(self.image_properties)

    def _buildCompositingLayoutWidget(self):
        compositing_group = gui.QgsCollapsibleGroupBox(_("Compositing"))
        compositing_group.setCollapsed(False)
        compositing_layout = QFormLayout()

        self.compositing_method = QComboBox(objectName="compositing_method")
        self.compositing_method.addItems(
            ["Mosaic", "Mean", "Max", "Min", "Median", "Percentile", "First"]
        )
        self.compositing_method.setToolTip(_("Select a compositing method."))
        compositing_layout.addRow(_("Compositing Method"), self.compositing_method)

        percentile_slider_layout = self._buildPercentileSliderLayout()
        compositing_layout.addRow(self.percentile_label, percentile_slider_layout)

        compositing_group.setLayout(compositing_layout)

        return compositing_group

    def _update_percentile_visibility(self, index):
        is_percentile = self.compositing_method.itemText(index) == "Percentile"
        self.percentile_label.setVisible(is_percentile)
        self.percentile_value.setVisible(is_percentile)
        self.percentile_max_label.setVisible(is_percentile)
        self.percentile_min_label.setVisible(is_percentile)
        self.percentile_current_value.setVisible(is_percentile)

    def _buildPercentileSliderLayout(self):
        self.percentile_label = QLabel(_("Percentile Value"))
        self.percentile_value = QSlider(objectName="percentile_value")
        self.percentile_value.setRange(0, 100)
        self.percentile_value.setSingleStep(1)
        self.percentile_value.setTickInterval(10)
        self.percentile_value.setOrientation(1)
        self.percentile_value.setTickPosition(QSlider.TicksBelow)
        self.percentile_min_label = QLabel("0")
        self.percentile_max_label = QLabel("100")

        self.percentile_current_value = QLabel(str(self.percentile_value.value()))
        self.percentile_value.valueChanged.connect(
            lambda value: self.percentile_current_value.setText(str(value))
        )

        percentile_slider_layout = QHBoxLayout()
        percentile_slider_layout.addWidget(self.percentile_min_label)
        percentile_slider_layout.addWidget(self.percentile_value)
        percentile_slider_layout.addWidget(self.percentile_max_label)
        # next line
        percentile_slider_layout.addSpacing(50)
        percentile_slider_layout.addWidget(self.percentile_current_value)

        self.percentile_value.setValue(50)
        self.percentile_value.setToolTip(_("Enter percentile value (0-100)"))
        self._update_percentile_visibility(self.compositing_method.currentIndex())

        return percentile_slider_layout

    def add_color_to_palette(self):
        options = QColorDialog.ColorDialogOptions(
            QColorDialog.ShowAlphaChannel | QColorDialog.DontUseNativeDialog
        )
        color_dialog = QColorDialog()
        color_dialog.setOptions(options)
        color = color_dialog.getColor()
        if color.isValid():
            hex_color = color.name()  # e.g. "#ff0000"
            self.color_palette.append(hex_color)

            # Display a swatch
            swatch = QLabel()
            swatch.setFixedSize(24, 24)
            swatch.setStyleSheet(
                f"background-color: {hex_color}; border: 1px solid black;"
            )
            self.palette_display.addWidget(swatch)

    def buildDialog(self) -> QWidget:
        # Build your custom layout
        layout = QVBoxLayout(self)

        # --- Source Group ---
        source_label = QLabel(
            _("Image Collection ID <br>(e.g. LANDSAT/LC09/C02/T1_L2)"),
        )
        source_label.setToolTip(_("The Earth Engine Image Collection ID."))
        self.image_collection_id = QLineEdit()
        self.image_collection_id.setObjectName("image_collection_id")
        self.image_collection_id.setToolTip(
            _("Enter the ID of the Earth Engine Image Collection.")
        )

        self.image_properties = []
        self.image_collection_id.textChanged.connect(
            self._on_image_collection_id_changed
        )
        self._update_timer = QTimer(
            self, singleShot=True, timeout=self._on_image_collection_id_ready
        )

        source_form = QFormLayout()
        source_form.addRow(source_label, self.image_collection_id)
        layout.addLayout(source_form)

        ## --- Filter by Properties ---
        self.filter_widget = FilterWidget(
            "Filter by Image Properties", self.image_properties
        )
        layout.addWidget(self.filter_widget)

        # --- Compositing Method ---
        compositing_group = self._buildCompositingLayoutWidget()
        layout.addWidget(compositing_group)
        self.compositing_method.currentIndexChanged.connect(
            self._update_percentile_visibility
        )

        # --- Filter by Dates ---
        date_group = gui.QgsCollapsibleGroupBox(_("Filter by Dates"))
        date_group.setCollapsed(False)
        date_layout = QFormLayout()
        self.start_date = gui.QgsDateEdit(objectName="start_date")
        self.start_date.setToolTip(_("Start date for filtering"))
        # keep empty dates
        self.start_date.setDate(QDate())
        self.end_date = gui.QgsDateEdit(objectName="end_date")
        self.end_date.setToolTip(_("End date for filtering"))
        self.end_date.setDate(QDate())  # default to today

        date_layout.addRow(_("Start"), self.start_date)
        date_layout.addRow(_("End"), self.end_date)
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)

        # --- Filter by Extent ---
        self.extent_group = gui.QgsExtentGroupBox(
            objectName="extent",
            title=_("Filter by Extent (Bounds)"),
            collapsed=True,
        )
        self.extent_group.setMapCanvas(Map.get_iface().mapCanvas())
        self.extent_group.setToolTip(_("Specify the geographic extent."))
        layout.addWidget(self.extent_group)

        # --- Visualization Parameters ---
        viz_group = gui.QgsCollapsibleGroupBox(_("Visualization Parameters"))
        viz_group.setCollapsed(False)
        self.viz_widget = VisualizationParamsWidget()
        viz_layout = QVBoxLayout()
        viz_layout.addWidget(self.viz_widget)
        viz_group.setLayout(viz_layout)

        # finally
        layout.addWidget(viz_group)

        return layout

    def update_band_dropdowns(self):
        band_selection_items = (
            get_available_bands(self.image_collection_id.text().strip(), silent=True)
            or []
        )
        for i in range(3):
            band_dropdown = self.findChild(QComboBox, f"viz_band_{i}")
            current = band_dropdown.currentText()
            band_dropdown.clear()
            band_dropdown.addItems(band_selection_items)
            band_dropdown.setCurrentText(current)

    def getParameters(self) -> dict:
        try:
            filters = []
            filter_layout = self.filter_widget.get_filter_rows_layout()
            for i in range(filter_layout.count()):
                row_layout = filter_layout.itemAt(i)
                if isinstance(row_layout, QHBoxLayout):
                    name_input = row_layout.itemAt(0).widget()
                    operator_input = row_layout.itemAt(1).widget()
                    value_input = row_layout.itemAt(2).widget()
                    if (
                        name_input
                        and value_input
                        and (name_input.currentText())
                        and value_input.text()
                    ):
                        op = operator_input.currentText()
                        name_val = name_input.currentText()
                        filters.append(f"{name_val}:{op}:{value_input.text()}")
            filters_str = ";".join(filters)

            # Build viz_params from UI
            selected_bands = []
            for i in range(3):
                band_dropdown = self.findChild(QComboBox, f"viz_band_{i}")
                if band_dropdown and band_dropdown.currentText():
                    selected_bands.append(band_dropdown.currentText())

            viz_params = self.viz_widget.get_viz_params()
            serialized = serialize_color_ramp(viz_params)
            viz_params["palette"] = serialized["palette"]
            extent = self.extent_group.outputExtent()
            params = {
                "image_collection_id": self.image_collection_id.text(),
                "filters": filters_str,
                "start_date": self.start_date.dateTime()
                if self.start_date.dateTime()
                else None,
                "end_date": self.end_date.dateTime()
                if self.end_date.dateTime()
                else None,
                "extent": (
                    f"{extent.xMinimum()},{extent.xMaximum()},{extent.yMinimum()},{extent.yMaximum()}"
                    if not extent.isEmpty()
                    else ""
                ),
                "compositing_method": self.compositing_method.currentIndex(),
                "percentile_value": self.percentile_value.value(),
                "viz_params": viz_params,
            }
            return params

        except Exception as e:
            raise ValueError(f"Invalid parameters: {e}")


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
        return "add_layer"

    def shortHelpString(self):
        return """
        <html>
        <b>Add Image Collection</b><br>
        This algorithm adds an Earth Engine Image Collection to the map with the specified compositing method and visualization parameters.<br>
        You can filter the collection by properties, dates, or geographic extent.<br>

        <h3>Parameters:</h3>
        <ul>
            <li><b>Image Collection ID:</b> The Earth Engine Image Collection <a href='https://developers.google.com/earth-engine/guides/manage_assets'>Asset ID</a> to add to the map.</li>
            <li><b>Filter Image Properties:</b> Image Property filter Filters to apply to the Image Collection. Image properties vary per dataset. See the <a href='https://developers.google.com/earth-engine/datasets'>Catalog</a> for details. 
            <li><b>End date for filtering:</b> The end date for filtering the Image Collection.</li>
            <li><b>Compositing Method:</b> The compositing method to use for the Image Collection.</li>
            <li><b>Percentile Value:</b> The percentile value to use for the 'Percentile' compositing method if selected.</li>
        <li><b>Visualization Parameters:</b> These include min, max, bands, palette (for single-band images), and gamma (for RGB or multi-band images). <br>
        Important: <code>gamma</code> and <code>palette</code> cannot be used together. Use <code>palette</code> only for single-band visualizations. <br>
        See the <a href='https://developers.google.com/earth-engine/guides/image_visualization' target='_blank'>Image Visualization Guide</a> for details.
        </li>
        </ul>

        <b>Earth Engine Data Catalog:</b>
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
                "Filter Image Properties",
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
                options=[
                    "Mosaic",
                    "Mean",
                    "Max",
                    "Min",
                    "Median",
                    "Percentile",
                    "First",
                ],
                optional=False,
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "percentile_value", "Percentile Value", optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "viz_params",
                "Visualization Parameters (JSON)",
                "Enter JSON for visualization parameters",
                optional=True,
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

    def createCustomParametersWidget(self, parent=...):
        return AddImageCollectionAlgorithmDialog(algorithm=self, parent=parent)

    def processAlgorithm(self, parameters, context, feedback):
        image_collection_id = parameters["image_collection_id"]
        filters = parameters["filters"]
        start_date = parameters["start_date"]
        end_date = parameters["end_date"]
        extent = parameters["extent"]  # This is the extent parameter as a string
        compositing_method = parameters["compositing_method"]
        percentile_value = (
            int(parameters["percentile_value"])
            if parameters["percentile_value"]
            else None
        )
        viz_params = parameters.get("viz_params", None)

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
        if not extent:
            logger.warning("Extent is not provided. The entire globe will be used.")
        if extent and isinstance(extent, str):
            # Parse extent from string format: "xmin,ymin,xmax,ymax [CRS]"
            try:
                coords = (
                    extent.split(" [")[0].replace(" : ", ",").replace(":", ",")
                )  # Normalize separator
                xmin, ymin, xmax, ymax = map(float, coords.split(","))
                extent = QgsRectangle(xmin, ymin, xmax, ymax)
                min_lon = extent.xMinimum()
                max_lon = extent.xMaximum()
                min_lat = extent.yMinimum()
                max_lat = extent.yMaximum()
                ee_extent = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])
                ic = ic.filterBounds(ee_extent)
            except Exception as e:
                raise ValueError(f"Invalid extent format: {extent}") from e

        # Apply the filters if provided
        if filters:
            filters = self._get_filters(filters)

            for filter_item in filters:
                filter_property, filter_operator, filter_value = filter_item
                filter_func = filter_functions.get(filter_operator)
                if filter_func:
                    # Attempt to convert value to number, fallback to string
                    try:
                        filter_value_casted = float(filter_value)
                        # Convert to int if applicable
                        if filter_value_casted.is_integer():
                            filter_value_casted = int(filter_value_casted)
                    except ValueError:
                        filter_value_casted = filter_value
                    ic = ic.filter(
                        filter_func["operator"](filter_property, filter_value_casted)
                    )

        # Apply compositing logic
        compositing_options = [
            "Mosaic",
            "Mean",
            "Max",
            "Min",
            "Median",
            "Percentile",
            "First",
        ]
        compositing_name = compositing_options[compositing_method]
        if compositing_name == "Mean":
            ic = ic.mean()
        elif compositing_name == "Max":
            ic = ic.max()
        elif compositing_name == "Min":
            ic = ic.min()
        elif compositing_name == "Median":
            ic = ic.median()
        elif compositing_name == "Percentile":
            if percentile_value is None:
                raise ValueError(
                    "Percentile value must be provided for 'Percentile' method."
                )
            if not (0 <= percentile_value <= 100):
                raise ValueError("Percentile value must be between 0 and 100.")
            ic = ic.reduce(ee.Reducer.percentile([percentile_value]))
        elif compositing_name == "First":
            logger.warning(
                "Using 'First' compositing method, which returns the first image in the collection."
            )
            ic = ic.first()
        elif compositing_name == "Mosaic":
            ic = ic.mosaic()
        else:
            raise ValueError(f"Unsupported compositing method: {compositing_name}")

        if isinstance(viz_params, str):
            try:
                viz_params = json.loads(viz_params.replace("'", '"'))
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON for visualization parameters.")
        elif not isinstance(viz_params, dict):
            raise ValueError(
                "Visualization parameters must be a JSON string or dictionary."
            )

        if compositing_name == "Percentile":
            name = f"IC: {image_collection_id} ({compositing_name} {percentile_value}%)"
        else:
            name = f"IC: {image_collection_id} ({compositing_name})"

        layer = Map.addLayer(ic, viz_params, name)

        return {"OUTPUT": layer, "LAYER_NAME": layer.name()}
