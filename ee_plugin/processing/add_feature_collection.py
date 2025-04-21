import re
import logging
from typing import List

import ee
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterString,
    QgsProcessingOutputVectorLayer,
    QgsProcessingOutputRasterLayer,
)
from qgis import gui
from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QCheckBox,
    QFormLayout,
    QSpinBox,
    QPushButton,
    QHBoxLayout,
    QWidget,
    QComboBox,
)

from .. import Map, utils
from ..ui.widgets import FilterWidget
from ..processing.custom_algorithm_dialog import BaseAlgorithmDialog
from ..utils import translate as _, get_ee_properties, filter_functions


logger = logging.getLogger(__name__)


class AddFeatureCollectionAlgorithm(QgsProcessingAlgorithm):
    def name(self):
        return "add_feature_collection"

    def displayName(self):
        return _("Add Feature Collection")

    def createInstance(self):
        return AddFeatureCollectionAlgorithm()

    def groupId(self):
        return "add_layer"

    def group(self):
        return "Add Layer"

    def shortHelpString(self):
        return """
    <html>
    <b>Add Feature Collection</b><br>
    This algorithm adds an Earth Engine Feature Collection to the map either as a styled vector layer (downloaded locally) or as a styled raster overlay.<br>
    You can filter the collection by properties, dates, or geographic extent.<br>
 
    <h3>Parameters:</h3>
    <ul>
        <li><b>Feature Collection ID:</b> The Earth Engine Feature Collection <a href='https://developers.google.com/earth-engine/guides/manage_assets'>Asset ID</a> to add to the map.</li>
        <li><b>Filter Properties:</b> Filters to apply to the Feature Collection. Feature properties vary per dataset. See the <a href='https://developers.google.com/earth-engine/datasets'>Catalog</a> for details.</li>
        <li><b>Start and End Date:</b> Optional start and end dates for filtering. Applies only to collections with <code>system:time_start</code>.</li>
        <li><b>Geographic Extent:</b> Optional bounding box filter using the format xmin,ymin,xmax,ymax.</li>
        <li><b>Visualization Parameters:</b> Includes outline color, fill color, line width, and opacity. These apply to both vector and raster styles.</li>
        <li><b>Retain as Vector Layer:</b> If checked, the features are downloaded as a local vector layer in QGIS use with caution for large datasets. Otherwise, the styled result is added as a raster overlay.</li>
    </ul>
 
    <b>Earth Engine Data Catalog:</b>
    <a href='https://developers.google.com/earth-engine/datasets'>https://developers.google.com/earth-engine/datasets</a>
    </html>
    """

    def initAlgorithm(self, config):
        # requires config in signature becuse of QGIS call to it
        self.addParameter(
            QgsProcessingParameterString(
                "feature_collection_id",
                _("Feature Collection ID"),
                defaultValue="",
            )
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
            QgsProcessingParameterString(
                "start_date",
                _("Start Date (YYYY-MM-DD)"),
                defaultValue="",
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                "end_date",
                _("End Date (YYYY-MM-DD)"),
                defaultValue="",
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                "extent",
                _("Extent (xmin,ymin,xmax,ymax)"),
                defaultValue="",
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                "viz_color_hex",
                _("Outline Color (Hex)"),
                defaultValue="#FF0000",
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                "viz_fill_color",
                _("Fill Color (Hex with alpha)"),
                defaultValue="#00000080",
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                "viz_width",
                _("Line Width"),
                defaultValue="2",
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                "opacity",
                _("Opacity (0-100)"),
                defaultValue="100",
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                "as_vector",
                _("Retain as Vector Layer"),
                defaultValue="false",
                optional=True,
            )
        )

        self.addOutput(
            QgsProcessingOutputVectorLayer(
                "OUTPUT_VECTOR",
                _("Output Vector Feature Collection"),
            )
        )

        self.addOutput(
            QgsProcessingOutputRasterLayer(
                "OUTPUT_RASTER",
                _("Output Feature Collection as XYZ Raster"),
            )
        )

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
        feature_collection_id = self.parameterAsString(
            parameters, "feature_collection_id", context
        )
        filters = self.parameterAsString(parameters, "filters", context)
        start_date = self.parameterAsString(parameters, "start_date", context)
        end_date = self.parameterAsString(parameters, "end_date", context)
        extent = self.parameterAsString(parameters, "extent", context)
        viz_color_hex = self.parameterAsString(parameters, "viz_color_hex", context)
        viz_fill_color = self.parameterAsString(parameters, "viz_fill_color", context)
        viz_width = self.parameterAsString(parameters, "viz_width", context)
        as_vector = self.parameterAsString(parameters, "as_vector", context)
        opacity = self.parameterAsString(parameters, "opacity", context)

        fc = ee.FeatureCollection(feature_collection_id)

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
                    fc = fc.filter(
                        filter_func["operator"](filter_property, filter_value_casted)
                    )

        # Apply date filter only if system:time_start exists
        if start_date and end_date and fc.size().getInfo() > 0:
            sample_feature = fc.first()
            sample_info = sample_feature.getInfo()
            if "system:time_start" in sample_info.get("properties", {}):
                fc = fc.filter(ee.Filter.date(ee.Date(start_date), ee.Date(end_date)))
            else:
                logger.warning(
                    "Skipping date filter: no system:time_start property found."
                )
        # Apply extent filter if provided
        if extent and extent.lower() != "null":
            try:
                # Split on commas and colons
                parts = re.split(r"[,:]", extent)
                coords = list(map(float, parts))
                if len(coords) == 4:
                    fc = fc.filterBounds(ee.Geometry.Rectangle(coords))
                else:
                    raise ValueError
            except Exception as e:
                raise ValueError(f"Invalid extent format: {extent}") from e

        # result can contain either vector or raster layer
        # depending on the as_vector parameter
        result = {}
        layer_name = f"FC: {feature_collection_id}"
        if as_vector.lower() in ("true", "1", "yes"):
            try:
                utils.add_ee_vector_layer(
                    fc,
                    layer_name,
                    shown=True,
                    style_params={
                        "color": viz_color_hex,
                        "fillColor": viz_fill_color,
                        "width": int(viz_width),
                        "opacity": int(opacity) / 100,
                    },
                )
                result["OUTPUT_VECTOR"] = layer_name
            except ee.ee_exception.EEException as e:
                logger.error(f"Failed to load the Feature Collection: {e}")
        else:
            styled_fc = fc.style(
                color=viz_color_hex, fillColor=viz_fill_color, width=int(viz_width)
            )
            # opacity can't be set from EE, we must apply in QGIS
            layer = Map.addLayer(styled_fc, {}, layer_name)
            if opacity != "":
                layer.setOpacity(int(opacity) / 100)
            result["OUTPUT_RASTER"] = layer

        if fc.size().getInfo() == 0:
            logger.warning(
                f"No features found in the Feature Collection: {feature_collection_id}"
            )

        return result

    def createCustomParametersWidget(self, parent=None):
        """Create a custom widget for the algorithm."""

        return AddFeatureCollectionAlgorithmDialog(self, parent=parent)


class AddFeatureCollectionAlgorithmDialog(BaseAlgorithmDialog):
    def __init__(self, algorithm, parent=None):
        self.feature_properties = []
        super().__init__(algorithm, parent)
        self._update_timer = QTimer(self, singleShot=True, timeout=self._on_fc_id_ready)

    def _build_visualization_group(self):
        group = gui.QgsCollapsibleGroupBox("Visualization")
        group.setCollapsed(True)
        layout = QFormLayout()

        self.outline_color = gui.QgsColorButton()
        self.outline_color.setObjectName("viz_color_hex")
        layout.addRow(QLabel("Outline Color"), self.outline_color)

        self.fill_color = gui.QgsColorButton()
        self.fill_color.setObjectName("viz_fill_color")
        layout.addRow(QLabel("Fill Color"), self.fill_color)

        self.line_width = QSpinBox()
        self.line_width.setMinimum(1)
        self.line_width.setMaximum(10)
        self.line_width.setValue(2)
        self.line_width.setObjectName("viz_width")
        layout.addRow(QLabel("Line Width (px)"), self.line_width)

        self.opacity = QSpinBox()
        self.opacity.setMinimum(0)
        self.opacity.setMaximum(100)
        self.opacity.setValue(100)
        self.opacity.setObjectName("opacity")
        layout.addRow(QLabel("Opacity (%)"), self.opacity)

        group.setLayout(layout)
        return group

    def _buildFilterLayoutWidget(self):
        filter_group = gui.QgsCollapsibleGroupBox(_("Filter by Properties"))
        filter_group.setCollapsed(True)

        self.filter_rows_layout = QVBoxLayout()

        def add_filter_row():
            row_layout = QHBoxLayout()

            name_input = QComboBox()
            name_input.setEditable(True)
            name_input.setToolTip(_("Enter or select a property name."))
            name_input.setObjectName("property_dropdown")
            name_input.addItems(self.feature_properties)

            operator_input = QComboBox()
            operator_input.addItems(["==", "!=", "<", ">", "<=", ">="])
            operator_input.setToolTip(_("Choose the filter operator."))

            value_input = QLineEdit()
            value_input.setPlaceholderText(_("Value"))
            value_input.setToolTip(_("Enter the value to filter by."))

            remove_button = QPushButton("Remove")

            def remove_row():
                for i in reversed(range(row_layout.count())):
                    widget = row_layout.itemAt(i).widget()
                    if widget:
                        widget.setParent(None)
                self.filter_rows_layout.removeItem(row_layout)

            remove_button.clicked.connect(remove_row)

            row_layout.addWidget(name_input, 2)
            row_layout.addWidget(operator_input, 1)
            row_layout.addWidget(value_input, 2)
            row_layout.addWidget(remove_button, 1)

            self.filter_rows_layout.addLayout(row_layout)

        add_filter_btn = QPushButton("Add Filter")
        add_filter_btn.clicked.connect(add_filter_row)
        add_filter_row()

        filter_widget = QWidget()
        filter_widget.setLayout(self.filter_rows_layout)

        filter_layout = QVBoxLayout()
        filter_layout.addWidget(filter_widget)
        filter_layout.addWidget(add_filter_btn)

        filter_group.setLayout(filter_layout)

        return filter_group

    def buildDialog(self):
        layout = QVBoxLayout()

        # --- Feature Collection ID ---
        self.fc_id = QLineEdit()
        self.fc_id.setPlaceholderText("e.g. USGS/WBD/2017/HUC06")
        # Connect signals
        self.fc_id.textChanged.connect(self._on_fc_id_changed)

        layout.addWidget(QLabel("Feature Collection ID"))
        layout.addWidget(self.fc_id)

        # --- Retain as Vector Layer ---
        self.as_vector = QCheckBox("Retain as vector layer")
        layout.addWidget(self.as_vector)

        # --- Filters ---
        self.filter_widget = FilterWidget(property_list=self.feature_properties)
        layout.addWidget(self.filter_widget)

        # --- Date Range ---
        date_group = gui.QgsCollapsibleGroupBox(_("Filter by Dates"))
        date_group.setCollapsed(True)
        date_layout = QFormLayout()
        self.start_date = gui.QgsDateEdit(objectName="start_date")
        self.start_date.setToolTip(_("Start date for filtering"))
        self.end_date = gui.QgsDateEdit(objectName="end_date")
        self.end_date.setToolTip(_("End date for filtering"))

        date_layout.addRow(_("Start"), self.start_date)
        date_layout.addRow(_("End"), self.end_date)
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)

        # --- Filter by Extent ---
        self.extent_group = gui.QgsExtentGroupBox(
            objectName="extent",
            title=_("Filter by Coordinates"),
            collapsed=True,
        )
        self.extent_group.setMapCanvas(Map.get_iface().mapCanvas())
        self.extent_group.setToolTip(_("Specify the geographic extent."))
        layout.addWidget(self.extent_group)

        # -- Visualization Parameters
        self.viz_group = self._build_visualization_group()
        layout.addWidget(self.viz_group)

        return layout

    def getParameters(self):
        filters = []
        filter_layout = self.filter_widget.get_filter_rows_layout()
        for i in range(filter_layout.count()):
            row_layout = filter_layout.itemAt(i)
            name_input = row_layout.itemAt(0).widget()
            operator_input = row_layout.itemAt(1).widget()
            value_input = row_layout.itemAt(2).widget()
            if (
                name_input
                and value_input
                and name_input.currentText()
                and value_input.text()
            ):
                op = operator_input.currentText()
                filters.append(f"{name_input.currentText()}:{op}:{value_input.text()}")
        filters_str = ";".join(filters)

        return {
            "feature_collection_id": self.fc_id.text().strip(),
            "as_vector": str(self.as_vector.isChecked()),
            "filters": filters_str,
            "start_date": self.start_date.date().toString("yyyy-MM-dd"),
            "end_date": self.end_date.date().toString("yyyy-MM-dd"),
            "extent": self.extent_group.outputExtent().toString(),
            "opacity": str(self.opacity.value()),
            "viz_color_hex": self.outline_color.color().name(),
            "viz_fill_color": self.fill_color.color().name(),
            "viz_width": str(self.line_width.value()),
        }

    def _on_fc_id_changed(self):
        self._update_timer.start(500)

    def _on_fc_id_ready(self):
        self.update_feature_properties()

    def update_feature_properties(self):
        asset_id = self.fc_id.text().strip()
        if not asset_id:
            return
        props = get_ee_properties(asset_id, silent=True)
        if props:
            self.feature_properties = props
            self._refresh_property_dropdowns()

    def _refresh_property_dropdowns(self):
        self.filter_widget.set_property_list(self.feature_properties)
