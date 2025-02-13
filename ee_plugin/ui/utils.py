import inspect
from dataclasses import field
from typing import Callable, List, Tuple, Union

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
from qgis.gui import (
    QgsColorButton,
    QgsCollapsibleGroupBox,
    QgsDateEdit,
    QgsExtentGroupBox,
)

from . import widget_parsers


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


def get_dialog_values(dialog: QDialog) -> dict:
    """
    Return a dictionary of all widget values from dialog.

    Note that the response dictionary may contain keys that were not explicitely set as
    object names in the widgets. This is due to the fact that some widgets are composites
    of multiple child widgets. The child widgets are parsed and stored in the response
    but it is the value of the parent widget that should be used in the application.
    """
    # NOTE: To support more widgets, register the widget class with a parser here. These
    # parsers are read in order, so more specific widgets should be listed last as their
    # results will overwrite more general widgets.
    parsers = {
        QLineEdit: lambda w: w.text(),
        QDateEdit: lambda w: w.date().toString("yyyy-MM-dd"),
        QgsDateEdit: lambda w: None if w.isNull() else w.findChild(QLineEdit).text(),
        QCheckBox: lambda w: w.isChecked(),
        QgsColorButton: lambda w: w.color().name(),
        QgsExtentGroupBox: widget_parsers.qgs_extent_to_bbox,
    }
    values = {}
    for cls, formatter in parsers.items():
        for widget in dialog.findChildren(cls):
            values[widget.objectName()] = formatter(widget)

    return values


def call_func_with_values(func: Callable, dialog: QDialog):
    """
    Call a function with values from a dialog. Prior to the call, the function signature
    is inspected and used to filter out any values from the dialog that are not expected
    by the function.
    """
    func_signature = inspect.signature(func)
    func_kwargs = set(func_signature.parameters.keys())
    dialog_values = get_dialog_values(dialog)
    kwargs = {k: v for k, v in dialog_values.items() if k in func_kwargs}
    return func(**kwargs)
