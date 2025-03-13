from typing import Optional

from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QDoubleSpinBox,
)
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.gui import QgsColorButton, QgsDateEdit, QgsExtentGroupBox


def qgs_extent_to_bbox(
    w: QgsExtentGroupBox,
) -> Optional[tuple[float, float, float, float]]:
    """
    Convert a QgsRectangle in a given CRS to an EPSG:4326 bounding box, formatted as
    (xmin, ymin, xmax, ymax).
    """
    extent = w.outputExtent()
    if extent.area() == float("inf"):
        return None

    source_crs = w.outputCrs()
    target_crs = QgsCoordinateReferenceSystem("EPSG:4326")

    extent_transformed = QgsCoordinateTransform(
        source_crs, target_crs, QgsProject.instance()
    ).transformBoundingBox(extent)

    return (
        extent_transformed.xMinimum(),
        extent_transformed.yMinimum(),
        extent_transformed.xMaximum(),
        extent_transformed.yMaximum(),
    )


def get_dialog_values(dialog: QDialog) -> dict:
    """
    Return a dictionary of all widget values from dialog.

    Note that the response dictionary may contain keys that were not explicitely set as
    object names in the widgets. This is due to the fact that some widgets are composites
    of multiple child widgets. The child widgets are parsed and stored in the response
    but it is the value of the parent widget that should be used in the application.
    """
    # NOTE: To support more widgets, the widget class must be registered here with a
    # parser. These parsers are read in order, so more specific widgets should be listed
    # last as their results will overwrite more general widgets.
    parsers = {
        QLineEdit: lambda w: w.text(),
        QDateEdit: lambda w: w.date().toString("yyyy-MM-dd"),
        QgsDateEdit: lambda w: None if w.isNull() else w.findChild(QLineEdit).text(),
        QTextEdit: lambda w: w.toPlainText(),
        QCheckBox: lambda w: w.isChecked(),
        QgsColorButton: lambda w: w.color().name(),
        QgsExtentGroupBox: qgs_extent_to_bbox,
        QComboBox: lambda w: w.currentText(),
        QDoubleSpinBox: lambda w: w.value(),
    }
    values = {}
    for cls, formatter in parsers.items():
        for widget in dialog.findChildren(cls):
            values[widget.objectName()] = formatter(widget)

    return values
