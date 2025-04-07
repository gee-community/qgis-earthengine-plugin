import re
import logging

import ee
from qgis.core import QgsProcessingAlgorithm, QgsProcessingParameterString
from qgis import gui
from qgis.PyQt.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QCheckBox,
    QFormLayout,
    QSpinBox,
)

from .. import Map, utils
from ..processing.custom_algorithm_dialog import BaseAlgorithmDialog
from ..utils import translate as _


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
        return _(
            "Adds a Google Earth Engine Feature Collection to the QGIS map.\n\n"
            "You can optionally filter the collection by property name/value pairs, "
            "date ranges, and bounding box coordinates. The resulting features can be "
            "added as a vector layer or visualized as a raster overlay with a specified color.\n\n"
            "Example dataset:  USGS/WBD/2017/HUC06\n"
            "<a href='https://developers.google.com/earth-engine/datasets/catalog'> Google Earth Engine Data Catalog</a> for more."
        )

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
                "filter_name",
                _("Filter Name"),
                defaultValue="",
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                "filter_value",
                _("Filter Value"),
                defaultValue="",
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
                "as_vector",
                _("Retain as Vector Layer"),
                defaultValue="false",
                optional=True,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        feature_collection_id = self.parameterAsString(
            parameters, "feature_collection_id", context
        )
        filter_name = self.parameterAsString(parameters, "filter_name", context)
        filter_value = self.parameterAsString(parameters, "filter_value", context)
        start_date = self.parameterAsString(parameters, "start_date", context)
        end_date = self.parameterAsString(parameters, "end_date", context)
        extent = self.parameterAsString(parameters, "extent", context)
        viz_color_hex = self.parameterAsString(parameters, "viz_color_hex", context)
        viz_fill_color = self.parameterAsString(parameters, "viz_fill_color", context)
        viz_width = self.parameterAsString(parameters, "viz_width", context)
        as_vector = self.parameterAsString(parameters, "as_vector", context)

        fc = ee.FeatureCollection(feature_collection_id)

        if filter_name and filter_value:
            fc = fc.filter(ee.Filter.eq(filter_name, filter_value))

        # Apply date filter only if system:time_start exists
        if start_date and end_date:
            sample_feature = fc.first()
            sample_info = sample_feature.getInfo()
            if "system:time_start" in sample_info.get("properties", {}):
                fc = fc.filter(ee.Filter.date(ee.Date(start_date), ee.Date(end_date)))
            else:
                logger.warning(
                    "Skipping date filter: no system:time_start property found."
                )

        if extent.lower() != "null":
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

        layer_name = f"FC: {feature_collection_id}"
        if as_vector.lower() in ("true", "1", "yes"):
            try:
                utils.add_ee_vector_layer(
                    fc,
                    layer_name,
                    shown=True,
                    opacity=1.0,
                    style_params={
                        "color": viz_color_hex,
                        "fillColor": viz_fill_color,
                        "width": int(viz_width),
                    },
                )
            except ee.ee_exception.EEException as e:
                logger.error(f"Failed to load the Feature Collection: {e}")
        else:
            styled_fc = fc.style(
                color=viz_color_hex, fillColor=viz_fill_color, width=int(viz_width)
            )
            Map.addLayer(styled_fc, {}, layer_name)

        return {"OUTPUT": fc}

    def createCustomParametersWidget(self, parent=None):
        """Create a custom widget for the algorithm."""

        return AddFeatureCollectionAlgorithmDialog(self, parent=parent)


class AddFeatureCollectionAlgorithmDialog(BaseAlgorithmDialog):
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

        group.setLayout(layout)

        return group

    def buildDialog(self):
        layout = QVBoxLayout()

        # --- Feature Collection ID ---
        self.fc_id = QLineEdit()
        self.fc_id.setPlaceholderText("e.g. USGS/WBD/2017/HUC06")
        layout.addWidget(QLabel("Feature Collection ID"))
        layout.addWidget(self.fc_id)

        # --- Retain as Vector Layer ---
        self.as_vector = QCheckBox("Retain as vector layer")
        layout.addWidget(self.as_vector)
        self.filter_name = QLineEdit()

        # -- Filters ---
        # TODO: support multiple and dynamic retrieval of properties
        # TODO: before, verify results without current filters for both retain and non retain vector
        layout.addWidget(QLabel("Filter name"))
        layout.addWidget(self.filter_name)
        self.filter_value = QLineEdit()
        layout.addWidget(QLabel("Filter value"))
        layout.addWidget(self.filter_value)

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
        return {
            "feature_collection_id": self.fc_id.text().strip(),
            "as_vector": str(self.as_vector.isChecked()),
            "filter_name": self.filter_name.text().strip(),
            "filter_value": self.filter_value.text().strip(),
            "start_date": self.start_date.date().toString("yyyy-MM-dd"),
            "end_date": self.end_date.date().toString("yyyy-MM-dd"),
            "extent": self.extent_group.outputExtent().toString(),
            "viz_color_hex": self.outline_color.color().name(),
            "viz_fill_color": self.fill_color.color().name(),
            "viz_width": str(self.line_width.value()),
        }
