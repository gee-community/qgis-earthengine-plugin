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
    QWidget,
    QFileDialog,
    QPushButton,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
)
from qgis.gui import QgsCollapsibleGroupBox


class FileSelectionWidget(QWidget):
    """
    A reusable widget for selecting a file using QFileDialog.
    Displays the selected file path in a QLineEdit.
    """

    def __init__(
        self,
        object_name: str = "file_path",
        caption: str = "Select File",
        filter: str = "All Files (*)",
        save_mode: bool = False,
        parent: QWidget = None,
        toolTip: str = None,
    ):
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setToolTip(toolTip)
        layout = QHBoxLayout(self)

        # Line edit to show selected file
        self.line_edit = QLineEdit(self)
        self.line_edit.setReadOnly(True)

        # Browse button
        self.button = QPushButton("Browse...", self)
        self.button.clicked.connect(self.open_file_dialog)

        # Add widgets to layout
        layout.addWidget(self.line_edit)
        layout.addWidget(self.button)
        self.setLayout(layout)

        # File dialog parameters
        self.caption = caption
        self.filter = filter
        self.save_mode = save_mode

    def open_file_dialog(self):
        """Open file dialog and update QLineEdit"""
        file_path, _ = (
            QFileDialog.getSaveFileName(None, self.caption, "", self.filter)
            if self.save_mode
            else QFileDialog.getOpenFileName(None, self.caption, "", self.filter)
        )
        if file_path:
            self.line_edit.setText(file_path)

    def get_selected_file(self) -> str:
        """Returns the selected file path"""
        return self.line_edit.text()


def DropdownWidget(
    object_name: str, options: list[str], toolTip: str = None
) -> QComboBox:
    """Creates a reusable dropdown (QComboBox) widget.

    Args:
        object_name (str): The name of the object (for referencing in dialogs).
        options (list[str]): A list of selectable options for the dropdown.

    Returns:
        QtWidgets.QComboBox: A populated dropdown widget.
    """
    dropdown = QComboBox(objectName=object_name, toolTip=toolTip)
    dropdown.addItems(options)
    return dropdown


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
