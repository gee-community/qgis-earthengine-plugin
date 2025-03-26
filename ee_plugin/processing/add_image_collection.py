from typing import List
import json
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

from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QDialogButtonBox,
    QSlider,
    QHBoxLayout,
    QWidget,
    QPushButton,
)
from qgis.core import QgsProject
from qgis import gui
from qgis import processing
from ..utils import translate as _

from .. import Map

filter_functions = {
    "==": {"operator": ee.Filter.eq, "symbol": "=="},
    "!=": {"operator": ee.Filter.neq, "symbol": "!="},
    "<": {"operator": ee.Filter.lt, "symbol": "<"},
    ">": {"operator": ee.Filter.gt, "symbol": ">"},
    "<=": {"operator": ee.Filter.lte, "symbol": "<="},
    ">=": {"operator": ee.Filter.gte, "symbol": ">="},
}


class AddImageCollectionAlgorithmDialog(QDialog):
    def __init__(self, alg, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Add Image Collection"))
        self.alg = alg
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

        source_form = QFormLayout()
        source_form.addRow(source_label, self.image_collection_id)
        layout.addLayout(source_form)

        # --- Filter by Properties ---
        filter_group = gui.QgsCollapsibleGroupBox(_("Filter by Properties"))
        filter_group.setCollapsed(True)

        self.filter_rows_layout = QVBoxLayout()

        def add_filter_row():
            row_layout = QHBoxLayout()

            name_input = QLineEdit()
            name_input.setPlaceholderText(_("Property Name"))
            name_input.setToolTip(_("Enter the property name to filter by."))

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

            row_layout.addWidget(name_input)
            row_layout.addWidget(operator_input)
            row_layout.addWidget(value_input)
            row_layout.addWidget(remove_button)

            self.filter_rows_layout.addLayout(row_layout)

        add_filter_btn = QPushButton("Add Filter")
        add_filter_btn.clicked.connect(add_filter_row)

        add_filter_row()  # Start with one filter row

        filter_widget = QWidget()
        filter_widget.setLayout(self.filter_rows_layout)

        filter_layout = QVBoxLayout()
        filter_layout.addWidget(filter_widget)
        filter_layout.addWidget(add_filter_btn)

        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # --- Compositing Method ---
        compositing_group = gui.QgsCollapsibleGroupBox(_("Compositing"))
        compositing_group.setCollapsed(False)
        compositing_layout = QFormLayout()

        self.compositing_method = QComboBox(objectName="compositing_method")
        self.compositing_method.addItems(
            ["Mosaic", "Mean", "Max", "Min", "Median", "Percentile"]
        )
        self.compositing_method.setToolTip(_("Select a compositing method."))
        compositing_layout.addRow(_("Compositing Method"), self.compositing_method)

        def update_percentile_visibility(index):
            is_percentile = self.compositing_method.itemText(index) == "Percentile"
            self.percentile_label.setVisible(is_percentile)
            self.percentile_value.setVisible(is_percentile)
            self.percentile_max_label.setVisible(is_percentile)
            self.percentile_min_label.setVisible(is_percentile)
            self.percentile_min_label.setVisible(is_percentile)
            self.percentile_max_label.setVisible(is_percentile)

        self.percentile_label = QLabel(_("Percentile Value"))
        self.percentile_value = QSlider(objectName="percentile_value")
        self.percentile_value.setRange(0, 100)
        self.percentile_value.setSingleStep(1)
        self.percentile_value.setTickInterval(10)
        self.percentile_value.setOrientation(1)
        self.percentile_value.setTickPosition(QSlider.TicksBelow)
        self.percentile_min_label = QLabel("0")
        self.percentile_max_label = QLabel("100")
        percentile_slider_layout = QHBoxLayout()
        percentile_slider_layout.addWidget(self.percentile_min_label)
        percentile_slider_layout.addWidget(self.percentile_value)
        percentile_slider_layout.addWidget(self.percentile_max_label)
        self.percentile_value.setValue(50)
        self.percentile_value.setToolTip(_("Enter percentile value (0-100)"))
        update_percentile_visibility(self.compositing_method.currentIndex())

        compositing_layout.addRow(self.percentile_label, percentile_slider_layout)

        compositing_group.setLayout(compositing_layout)
        layout.addWidget(compositing_group)

        # Show/hide percentile input based on method

        self.compositing_method.currentIndexChanged.connect(
            update_percentile_visibility
        )

        # --- Filter by Dates ---
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

        # --- Filter by Coordinates ---
        self.extent_group = gui.QgsExtentGroupBox(
            objectName="extent",
            title=_("Filter by Coordinates"),
            collapsed=True,
        )
        self.extent_group.setToolTip(_("Specify the geographic extent."))
        layout.addWidget(self.extent_group)

        # --- Dialog Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.run_algorithm)  # Connect to new method
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def run_algorithm(self):
        # Collect parameters from form widgets
        filters = []
        for i in range(self.filter_rows_layout.count()):
            row_layout = self.filter_rows_layout.itemAt(i)
            if isinstance(row_layout, QHBoxLayout):
                name_input = row_layout.itemAt(0).widget()
                operator_input = row_layout.itemAt(1).widget()
                value_input = row_layout.itemAt(2).widget()
                if (
                    name_input
                    and value_input
                    and name_input.text()
                    and value_input.text()
                ):
                    op = operator_input.currentText()
                    filters.append(f"{name_input.text()}:{op}:{value_input.text()}")
        filters_str = ";".join(filters)

        params = {
            "image_collection_id": self.image_collection_id.text(),
            "filters": filters_str,
            "start_date": self.start_date.dateTime(),
            "end_date": self.end_date.dateTime(),
            "extent": self.extent_group.outputExtent(),
            "compositing_method": self.compositing_method.currentIndex(),
            "percentile_value": self.percentile_value.value(),
            "viz_params": "{}",  # optionally make this a field in the UI
        }

        # Run the algorithm
        result = processing.run("ee:add_image_collection", params)
        if result:
            QgsProject.instance().layerTreeRoot().addLayer(result["OUTPUT"])
            self.accept()


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
            <li><b>Image Collection ID:</b> The Earth Engine Image Collection ID to add to the map.</li>
            <li><b>Filters:</b> The filter type to apply to the Image Collection. Example: "cloud_coverage:&lt;:10;sun_elevation:&gt;:0" for non-cloudy daytime Landsat images.</li>
            <li><b>Start date for filtering:</b> The start date for filtering the Image Collection.</li>
            <li><b>End date for filtering:</b> The end date for filtering the Image Collection.</li>
            <li><b>Compositing Method:</b> The compositing method to use for the Image Collection.</li>
            <li><b>Percentile Value:</b> The percentile value to use for the 'Percentile' compositing method if selected.</li>
            <li><b>Visualization Parameters:</b> JSON string for visualization parameters.</li>
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
        return AddImageCollectionAlgorithmDialog(self, parent)

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
        if extent:
            min_lon = extent.xMinimum()
            max_lon = extent.xMaximum()
            min_lat = extent.yMinimum()
            max_lat = extent.yMaximum()
            ee_extent = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])
            ic = ic.filterBounds(ee_extent)

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
        compositing_dict = {
            "Mean": ic.mean(),
            "Max": ic.max(),
            "Min": ic.min(),
            "Median": ic.median(),
            "Percentile": ic.reduce(ee.Reducer.percentile([percentile_value])),
        }

        ic = compositing_dict.get(compositing_method, ic.mosaic())

        # Add the image collection to the map
        if compositing_method == "Percentile":
            if percentile_value is None:
                raise ValueError(
                    "Percentile value is required for 'Percentile' method."
                )
            if percentile_value < 0 or percentile_value > 100:
                raise ValueError("Percentile value must be between 0 and 100.")

        if viz_params:
            try:
                viz_params = json.loads(viz_params)  # Parse the JSON string
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON for visualization parameters.")
        else:
            viz_params = {}

        # compositing method is an index
        compositing_options = ["Mosaic", "Mean", "Max", "Min", "Median", "Percentile"]
        compositing_name = compositing_options[compositing_method]
        if compositing_method == "Percentile":
            name = f"IC: {image_collection_id} ({compositing_name} {percentile_value}%)"
        else:
            name = f"IC: {image_collection_id} ({compositing_name})"

        layer = Map.addLayer(ic, viz_params, name)

        return {"OUTPUT": layer, "LAYER_NAME": layer.name()}
