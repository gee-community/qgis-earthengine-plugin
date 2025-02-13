from typing import Optional

from qgis.gui import QgsExtentGroupBox
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject


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
