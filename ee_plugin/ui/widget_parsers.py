from typing import Optional

from qgis.gui import QgsExtentGroupBox
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject


def qgs_extent_to_bbox(
    w: QgsExtentGroupBox,
) -> Optional[tuple[float, float, float, float]]:
    """
    Convert a QgsRectangle in a given CRS to an Earth Engine ee.Geometry.Rectangle.

    :param rect: A QgsRectangle representing the bounding box.
    :param source_crs: The CRS in which rect is defined (e.g., QgsCoordinateReferenceSystem("EPSG:XXXX")).
    :param target_crs: The CRS to transform to. Defaults to EPSG:4326 (WGS84 lat/lon).
    :return: An ee.Geometry.Rectangle in the target CRS (default: EPSG:4326).
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
