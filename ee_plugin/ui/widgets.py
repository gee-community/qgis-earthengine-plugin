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
)
from qgis.gui import QgsCollapsibleGroupBox


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
