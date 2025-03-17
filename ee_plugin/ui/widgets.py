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
)
from qgis.gui import QgsCollapsibleGroupBox


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

        # Layout
        layout = QVBoxLayout(self)

        # Label to display the value
        self.label = QLabel(f"{label}")
        layout.addWidget(self.label)
        # keep to have more visibility on value of slider
        self.initial_label = label
        self.update_label(default_value)

        # Slider setup
        self.slider = QSlider(QtCore.Qt.Horizontal)
        # TODO: add min and max value to scale the slider visually

        self.slider.setRange(min_value, max_value)
        self.slider.setValue(default_value)
        layout.addWidget(self.slider)

        # Connect slider to update label
        self.slider.valueChanged.connect(self.update_label)

        # Set visibility
        self.set_visibility(visible)

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
