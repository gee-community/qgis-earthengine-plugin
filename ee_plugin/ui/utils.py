from dataclasses import dataclass, field
from typing import List, Optional, Type, Callable, Tuple

from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QGroupBox,
    QFormLayout,
    QVBoxLayout,
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QDateEdit,
    QCheckBox,
)


IGNORED_TYPES = (QLabel, QGroupBox, QDialogButtonBox, QVBoxLayout, QFormLayout)


def build_label(
    *,
    object_name: str,
    text: str,
    tooltip: Optional[str] = None,
    whatsthis: Optional[str] = None,
    cls: Type[QLabel] = QLabel,
    parent: Optional[QWidget] = None,
) -> QLabel:
    """
    Defines a QLabel with optional tooltip/WhatsThis.
    """
    lbl = cls(parent)
    lbl.setObjectName(object_name)
    lbl.setText(text)
    if tooltip:
        lbl.setToolTip(tooltip)
    if whatsthis:
        lbl.setWhatsThis(whatsthis)

    return lbl


def build_widget(
    *,
    object_name: str,
    cls: Type,
    **kwargs,
) -> QWidget:
    """
    Describes the widget to be created (e.g., QLineEdit, QDateEdit, QgsColorButton),
    storing the actual widget class instead of a string.
    """
    widget = cls(**kwargs)
    widget.setObjectName(object_name)
    return widget


@dataclass
class Row:
    """
    A row in a QFormLayout: label + widget side by side.
    """

    label: QLabel
    widget: QWidget


def build_group_box(
    *,
    object_name: str,
    title: str,
    rows: List[Tuple[QWidget, QWidget]] = field(default_factory=list),
) -> QGroupBox:
    """
    A group box in the UI.

    :param object_name: The object name of the group box.
    :param title: The title of the group box.
    :param rows: A list of tuples, each containing a label and a widget.
    """
    gb = QGroupBox()
    gb.setObjectName(object_name)
    gb.setTitle(title)

    form_layout = QFormLayout(gb)
    gb.setLayout(form_layout)

    for row in rows:
        form_layout.addRow(*row)

    return gb


def build_button_box(
    *,
    object_name: str,
    buttons: List[QDialogButtonBox.StandardButton] = field(default_factory=list),
    accepted: Optional[Callable] = None,
    rejected: Optional[Callable] = None,
) -> QDialogButtonBox:
    """
    A button box in the UI.
    """
    btn_box = QDialogButtonBox()
    btn_box.setObjectName(object_name)

    for button in buttons:
        btn_box.addButton(button)

    if accepted:
        btn_box.accepted.connect(accepted)
    if rejected:
        btn_box.rejected.connect(rejected)

    return btn_box


def build_dialog(
    object_name: str,
    title: str,
    width: int = 600,
    height: int = 400,
    margins: tuple = (10, 10, 10, 10),
    children: List[QWidget] = field(default_factory=list),
    parent: Optional[QWidget] = None,
) -> QDialog:
    """
    The top-level definition of our dialog window.
    It holds the dialog's dimensions, title, margins, and the group boxes to be displayed.

    The build() method creates and returns a QDialog, setting up the layout,
    adding each group box in turn, and finally adding a standard button box (OK/Cancel).
    """

    """
    Create the QDialog, set its layout and geometry, build group boxes,
    add the button box, and return the dialog widget.

    :return: A tuple: (QDialog instance, Dict of widget references).
    """
    dialog = QDialog(parent)
    dialog.setObjectName(object_name)
    dialog.setWindowTitle(title)
    dialog.resize(width, height)

    main_layout = QVBoxLayout(dialog)
    main_layout.setContentsMargins(*margins)
    dialog.setLayout(main_layout)

    # Build each group box
    for widget in children:
        main_layout.addWidget(widget)

    # Add OK/Cancel buttons
    main_layout.addWidget(
        build_button_box(
            object_name="button_box",
            buttons=[QDialogButtonBox.Ok, QDialogButtonBox.Cancel],
            accepted=dialog.accept,
            rejected=dialog.reject,
        )
    )

    return dialog


def get_values(dialog):
    """
    Return a dictionary of all widget values from dialog.
    """
    parsers = {
        QLineEdit: lambda w: w.text(),
        QDateEdit: lambda w: w.date().toString("yyyy-MM-dd"),
        QCheckBox: lambda w: w.isChecked(),
    }
    return {
        w.objectName(): parsers[type(w)](w)
        for w in dialog.findChildren(QWidget)
        if type(w) in parsers
    }
