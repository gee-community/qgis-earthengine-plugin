from qgis.core import QgsPointXY, QgsRectangle

from ee_plugin.utils import geom_to_geo


def test_qgs_point_geom_to_geo():
    point = QgsPointXY(1.5, 1.5)
    assert geom_to_geo(point) == QgsPointXY(1.5, 1.5), "Point conversion failed"


def test_qgs_rect_geom_to_geo():
    rect = QgsRectangle(-40, -20, 40, 20)
    assert geom_to_geo(rect) == QgsRectangle(
        -40, -20, 40, 20
    ), "Rectangle conversion failed"
