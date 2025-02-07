from dataclasses import dataclass, field
from typing import List, Optional, Type

from qgis.PyQt.QtWidgets import (
    QWidget,
    QLabel,
    QGroupBox,
    QFormLayout,
    QVBoxLayout,
    QDialog,
    QDialogButtonBox,
)


@dataclass
class Label:
    """
    Defines a QLabel with optional tooltip/whatsThis.
    """

    object_name: str
    text: str
    tooltip: Optional[str] = None
    whatsthis: Optional[str] = None
    cls: Type[QLabel] = QLabel

    def build(self, parent: QWidget) -> QLabel:
        """Instantiate and return a QLabel."""
        label = self.cls(parent)
        label.setObjectName(self.object_name)
        label.setText(self.text)
        if self.tooltip:
            label.setToolTip(self.tooltip)
        if self.whatsthis:
            label.setWhatsThis(self.whatsthis)
        return label


@dataclass
class Widget:
    """
    Describes the widget to be created (e.g., QLineEdit, QDateEdit, QgsColorButton).
    Storing the actual widget class instead of a string.
    """

    cls: Type
    object_name: str

    def build(self, parent: QWidget) -> QWidget:
        """Instantiate and return a widget of the given class."""
        w = self.cls(parent)
        w.setObjectName(self.object_name)
        return w


@dataclass
class Row:
    """
    A row in a QFormLayout: label + widget side by side.
    """

    label: Label
    widget: Widget

    def build(self, parent: QWidget, form_layout: QFormLayout):
        """
        Create a label and widget, then add them to the form layout.
        Returns (label_instance, widget_instance).
        """
        lbl = self.label.build(parent)
        wdg = self.widget.build(parent)
        form_layout.addRow(lbl, wdg)
        return lbl, wdg


@dataclass
class GroupBox:
    """
    A group box in the UI. If `stretch_factor` is provided, that determines
    how tall this block grows relative to other siblings in the parent layout.
    """

    object_name: str
    title: str
    rows: List[Row] = field(default_factory=list)
    stretch_factor: Optional[int] = None

    def build(self, parent: QWidget, parent_layout: QVBoxLayout) -> QGroupBox:
        """
        Create a QGroupBox, give it a QFormLayout, build each row,
        then add this group box to the parent_layout (with optional stretch).
        Returns the newly created QGroupBox instance.
        """
        gb = QGroupBox(parent)
        gb.setObjectName(self.object_name)
        gb.setTitle(self.title)

        form_layout = QFormLayout(gb)
        for row in self.rows:
            row.build(gb, form_layout)

        if self.stretch_factor is not None:
            parent_layout.addWidget(gb, self.stretch_factor)
        else:
            parent_layout.addWidget(gb)

        return gb


@dataclass
class Dialog:
    """
    The top-level definition of our dialog window.
    It holds the dialog's dimensions, title, margins, and the group boxes to be displayed.

    The build() method creates and returns a QDialog, setting up the layout,
    adding each group box in turn, and finally adding a standard button box (OK/Cancel).
    """

    object_name: str
    title: str
    width: int = 600
    height: int = 400
    margins: tuple = (10, 10, 10, 10)
    group_boxes: List[GroupBox] = field(default_factory=list)

    def build(self, parent) -> QDialog:
        """
        Create the QDialog, set its layout and geometry, then build the group boxes
        and the button box at the bottom. Returns the fully constructed dialog.
        """
        dialog = QDialog(parent)
        dialog.setObjectName(self.object_name)
        dialog.setWindowTitle(self.title)
        dialog.resize(self.width, self.height)

        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(*self.margins)
        dialog.setLayout(main_layout)

        # Build each group box in order
        for gb_def in self.group_boxes:
            gb_def.build(dialog, main_layout)

        # Add OK/Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.setObjectName("buttonBox")
        main_layout.addWidget(button_box)

        # Hook up signals
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        return dialog
