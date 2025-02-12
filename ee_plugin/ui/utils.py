from dataclasses import field
from typing import List, Tuple, Union

from qgis.PyQt.QtWidgets import (
    QWidget,
    QGroupBox,
    QFormLayout,
    QVBoxLayout,
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QDateEdit,
    QCheckBox,
    QLayout,
)
from qgis.gui import QgsColorButton, QgsCollapsibleGroupBox


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


def get_values(dialog: QDialog) -> dict:
    """
    Return a dictionary of all widget values from dialog.
    """
    parsers = {
        QLineEdit: lambda w: w.text(),
        QDateEdit: lambda w: w.date().toString("yyyy-MM-dd"),
        QgsDateEdit: lambda w: None if w.isNull() else w.findChild(QLineEdit).text(),
        QCheckBox: lambda w: w.isChecked(),
        QgsColorButton: lambda w: w.color().name(),
    }
    values = {}
    # TODO: Some widgets have subwidgets with different names, need to reasonbly handle this
    for cls, formatter in parsers.items():
        for widget in dialog.findChildren(cls):
            values[widget.objectName()] = formatter(widget)

    return values
