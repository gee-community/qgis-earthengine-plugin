from dataclasses import field
from typing import List, Optional, Tuple, Union

from qgis import gui
from qgis.PyQt import QtCore
from qgis.PyQt.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLayout,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QWidget,
    QPushButton,
    QSlider,
    QLabel,
    QDoubleSpinBox,
    QColorDialog,
)
from qgis.gui import QgsCollapsibleGroupBox

from ..utils import translate as _


class LabeledSlider(QWidget):
    """
    A labeled slider widget that displays the selected value.

    Args:
        min_value (int): The minimum value of the slider.
        max_value (int): The maximum value of the slider.
        default_value (int): The default starting value.
        object_name (str): The object name for the widget.
        visible (bool): Whether the widget should be visible initially.
    """

    def __init__(
        self,
        min_value: int = 0,
        max_value: int = 100,
        default_value: int = 50,
        object_name="slider",
        label: str = None,
        visible: bool = False,
    ):
        super().__init__()
        self.setObjectName(object_name)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Top label showing the current value
        self.label = QLabel()
        self.initial_label = label or "Value"
        self.update_label(default_value)
        main_layout.addWidget(self.label)

        # Slider setup
        self.slider = QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(min_value, max_value)
        self.slider.setValue(default_value)

        # Min/Max labels beside the slider
        min_label = QLabel(str(min_value))
        max_label = QLabel(str(max_value))

        # Layout for slider with min/max
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(min_label)
        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(max_label)

        main_layout.addLayout(slider_layout)

        # Update value label when slider moves
        self.slider.valueChanged.connect(self.update_label)

        # Initial visibility
        self.setVisible(visible)

    def update_label(self, value):
        """Update label text with the current slider value."""
        self.label.setText(f"{self.initial_label}: {value}")

    def set_visibility(self, visible: bool):
        """Toggle visibility of the widget."""
        self.setVisible(visible)
        self.label.setVisible(visible)

    def get_value(self) -> int:
        """Get the current value of the slider."""
        return self.slider.value()

    def set_value(self, value: int):
        """Set the current value of the slider."""
        self.slider.setValue(value)


def create_filter_widget() -> QWidget:
    filter_widget = QWidget()
    filter_widget.setObjectName("filter_widget")
    layout = QVBoxLayout()
    filter_widget.setLayout(layout)

    # Use a simple global counter for unique filter IDs
    global filter_count
    filter_count = 0

    def add_filter():
        global filter_count
        row = QHBoxLayout()

        # Create unique object names using filter_count
        name_input = QLineEdit()
        name_input.setPlaceholderText("Property Name")
        name_input.setToolTip(
            "Enter the property name to filter by (e.g., CLOUD_COVER)."
        )
        name_input.setObjectName(f"filter_name_{filter_count}")
        row.addWidget(name_input)

        operator_combo = QComboBox()
        operator_combo.addItems(
            [
                "Equals (==)",
                "Not Equals (!=)",
                "Less Than (<)",
                "Greater Than (>)",
                "Less Than or Equal (<=)",
                "Greater Than or Equal (>=)",
            ]
        )
        operator_combo.setToolTip("Choose the operator for filtering.")
        operator_combo.setObjectName(f"filter_operator_{filter_count}")
        row.addWidget(operator_combo)

        value_input = QLineEdit()
        value_input.setPlaceholderText("Value")
        value_input.setToolTip(
            "Enter the value to filter by (can be numeric or string)."
        )
        value_input.setObjectName(f"filter_value_{filter_count}")
        row.addWidget(value_input)

        remove_button = QPushButton("Remove")
        remove_button.setToolTip("Remove this filter.")
        remove_button.clicked.connect(lambda: remove_filter(row))
        row.addWidget(remove_button)

        layout.addLayout(row)

        # Increment global counter for the next filter
        filter_count += 1

    def remove_filter(row):
        # Remove all widgets in the row
        for i in reversed(range(row.count())):
            widget = row.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        layout.removeItem(row)

    add_filter_button = QPushButton("Add Filter")
    add_filter_button.setObjectName("add_filter_button")
    add_filter_button.setToolTip("Click to add a new property filter.")
    add_filter_button.clicked.connect(add_filter)
    layout.addWidget(add_filter_button)

    # Initialize with one filter row
    add_filter()

    return filter_widget


def DefaultNullQgsDateEdit(
    *, date: Optional[QtCore.QDate] = None, displayFormat="yyyy-MM-dd", **kwargs
) -> gui.QgsDateEdit:
    """Build a QgsDateEdit widget, with null default capability."""
    # NOTE: Specifying a displayFormat guarantees that the date will be formatted as
    # expected across different runtime environments.
    d = gui.QgsDateEdit(**kwargs, displayFormat=displayFormat)
    # NOTE: It would be great to remove this helper and just use the built-in QgsDateEdit
    # class but at this time it's not clear how to make a DateEdit widget that initializes
    # with a null value. This is a workaround.
    if date is None:
        d.clear()
    else:
        d.setDate(date)
    return d


def build_form_group_box(
    *,
    rows: List[
        Union[Tuple[Union[QWidget, str], Union[QWidget, QLayout]], QWidget, QLayout]
    ] = field(default_factory=list),
    collapsable: bool = False,
    **kwargs,
) -> Union[QGroupBox, QgsCollapsibleGroupBox]:
    """
    A group box with a form layout.
    """
    gb = QGroupBox(**kwargs) if not collapsable else QgsCollapsibleGroupBox(**kwargs)
    layout = QFormLayout()
    gb.setLayout(layout)

    for row in rows:
        if isinstance(row, (QWidget, QLayout)):
            row = [row]
        layout.addRow(*row)

    return gb


def build_vbox_dialog(
    widgets: List[QWidget] = field(default_factory=list),
    show: bool = True,
    **kwargs,
) -> QDialog:
    """
    Build a dialog with a vertical layout and configured standard buttons.
    """
    dialog = QDialog(**kwargs)

    # Configure dialog layout
    main_layout = QVBoxLayout(dialog)
    dialog.setLayout(main_layout)

    # Add widgets to the dialog
    for widget in widgets:
        main_layout.addWidget(widget)

    # Add OK/Cancel buttons
    main_layout.addWidget(
        QDialogButtonBox(
            standardButtons=QDialogButtonBox.Cancel | QDialogButtonBox.Ok,
            accepted=dialog.accept,
            rejected=dialog.reject,
        )
    )

    # Show the dialog on screen
    if show:
        dialog.show()

    return dialog


def build_vbox_widget(
    widgets: List[QWidget] = field(default_factory=list),
    **kwargs,
) -> QWidget:
    """
    Build a widget with a vertical layout and configured standard buttons.
    """
    container = QWidget(**kwargs)

    # Configure layout
    main_layout = QVBoxLayout(container)

    # Add widgets to the layout
    for widget in widgets:
        main_layout.addWidget(widget)

    # Add OK/Cancel buttons
    main_layout.addWidget(
        QDialogButtonBox(
            standardButtons=QDialogButtonBox.Cancel | QDialogButtonBox.Ok,
        )
    )

    return container


class VisualizationParamsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.color_palette = []
        self.layout = QFormLayout()

        # Band selection
        self.band_selection = [QComboBox(self) for _ in range(3)]
        bands_layout = QHBoxLayout()
        for i, combo in enumerate(self.band_selection):
            combo.setObjectName(f"viz_band_{i}")
            combo.setEditable(True)
            combo.setPlaceholderText("Band")
            bands_layout.addWidget(combo)
        self.layout.addRow(QLabel("Select Bands (RGB)"), bands_layout)

        # Color palette
        self.color_palette = []
        self.add_color_btn = QPushButton("Add Color")
        self.add_color_btn.clicked.connect(self.add_color_to_palette)
        self.palette_display = QHBoxLayout()
        palette_widget = QWidget()
        palette_widget.setLayout(self.palette_display)
        self.layout.addRow(QLabel("Color Palette"), self.add_color_btn)
        self.layout.addRow(palette_widget)

        # min, max, gamma, opacity
        self.viz_min = self._make_spinbox(-1e6, 1e6, "Min")
        self.viz_max = self._make_spinbox(-1e6, 1e6, "Max", default=10000)
        self.viz_gamma = self._make_spinbox(0.01, 10.0, "Gamma")
        self.viz_opacity = self._make_spinbox(0.01, 1.0, "Opacity", default=1.0)

        self.setLayout(self.layout)

    def _make_spinbox(self, min_val, max_val, label, default=None):
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setDecimals(2)
        spin.setSingleStep(0.1)
        if default is not None:
            spin.setValue(default)
        self.layout.addRow(QLabel(label), spin)
        setattr(self, f"viz_{label.lower()}", spin)
        return spin

    def add_color_to_palette(self):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name()
            self.color_palette.append(hex_color)
            swatch = QLabel()
            swatch.setFixedSize(24, 24)
            swatch.setStyleSheet(
                f"background-color: {hex_color}; border: 1px solid black;"
            )
            self.palette_display.addWidget(swatch)

    def get_viz_params(self):
        bands = [
            combo.currentText() for combo in self.band_selection if combo.currentText()
        ]
        params = {
            "bands": bands,
            "min": self.viz_min.value(),
            "max": self.viz_max.value(),
            "opacity": self.viz_opacity.value(),
        }
        if self.color_palette:
            params["palette"] = self.color_palette
        else:
            params["gamma"] = self.viz_gamma.value()
        return params


class FilterWidget(gui.QgsCollapsibleGroupBox):
    def __init__(self, title="Filter by Properties", property_list=None, parent=None):
        super().__init__(title, parent)
        self.setCollapsed(True)
        self.property_list = property_list or []
        self.filter_rows_layout = QVBoxLayout()
        self._build_filter_widget()

    def _build_filter_widget(self):
        def add_filter_row():
            row_layout = QHBoxLayout()

            name_input = QComboBox()
            name_input.setEditable(True)
            name_input.setToolTip(_("Enter or select a property name."))
            name_input.setObjectName("property_dropdown")
            name_input.addItems(self.property_list)

            operator_input = QComboBox()
            operator_input.addItems(["==", "!=", "<", ">", "<=", ">="])
            operator_input.setToolTip(_("Choose the filter operator."))

            value_input = QLineEdit()
            value_input.setPlaceholderText(_("Value"))
            value_input.setToolTip(_("Enter the value to filter by."))

            remove_button = QPushButton("Remove")
            remove_button.clicked.connect(lambda: self._remove_row(row_layout))

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

        layout = QVBoxLayout()
        layout.addWidget(filter_widget)
        layout.addWidget(add_filter_btn)
        self.setLayout(layout)

    def _remove_row(self, row_layout):
        for i in reversed(range(row_layout.count())):
            widget = row_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.filter_rows_layout.removeItem(row_layout)

    def set_property_list(self, props):
        self.property_list = props
        for i in range(self.filter_rows_layout.count()):
            layout = self.filter_rows_layout.itemAt(i)
            if isinstance(layout, QHBoxLayout):
                dropdown = layout.itemAt(0).widget()
                if isinstance(dropdown, QComboBox):
                    dropdown.clear()
                    dropdown.addItems(self.property_list)

    def get_filter_rows_layout(self):
        return self.filter_rows_layout
