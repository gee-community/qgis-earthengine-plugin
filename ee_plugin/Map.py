# -*- coding: utf-8 -*-
"""
functions to use GEE within Qgis python script
"""

import math

import ee
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsPointXY,
    QgsProject,
    QgsRectangle,
)
from qgis import gui
from qgis.PyQt.QtCore import QEventLoop, QTimer, QCoreApplication, QThread

from . import utils


def get_iface() -> gui.QgisInterface:
    # Lazy import to ensure that iface is available after gqis is initialized
    from qgis.utils import iface

    if not iface:
        raise ImportError("QGIS interface not available. Has QGIS been initialized?")
    return iface


def addLayer(eeObject, visParams=None, name=None, shown=True, opacity=1.0):
    """
    Adds a given EE object to the map as a layer.

    https://developers.google.com/earth-engine/api_docs#mapaddlayer

    Uses:
        >>> from ee_plugin import Map
        >>> Map.addLayer(.....)
    """
    utils.add_or_update_ee_layer(eeObject, visParams, name, shown, opacity)


def centerObject(feature, zoom=None):
    """
    Centers the map view on a given object.

    https://developers.google.com/earth-engine/api_docs#mapcenterobject

    Uses:
        >>> from ee_plugin import Map
        >>> Map.centerObject(feature)
    """

    if not hasattr(feature, "geometry"):
        feature = ee.Feature(feature)

    if not zoom:
        # make sure our geometry is in geo
        rect = feature.geometry().transform(ee.Projection("EPSG:4326"), 1)

        # get coordinates
        coords = rect.bounds().getInfo()["coordinates"][0]
        xmin = coords[0][0]
        ymin = coords[0][1]
        xmax = coords[2][0]
        ymax = coords[2][1]

        # construct QGIS geometry
        rect = QgsRectangle(xmin, ymin, xmax, ymax)

        # transform rect to a crs used by current project
        crs_src = QgsCoordinateReferenceSystem("EPSG:4326")
        crs_dst = QgsCoordinateReferenceSystem(QgsProject.instance().crs())
        geo2proj = QgsCoordinateTransform(crs_src, crs_dst, QgsProject.instance())
        rect_proj = geo2proj.transform(rect)

        # center geometry
        iface = get_iface()
        iface.mapCanvas().zoomToFeatureExtent(rect_proj)
    else:
        # set map center to feature centroid at a specified zoom
        center = feature.geometry().centroid().coordinates().getInfo()
        setCenter(center[0], center[1], zoom)


def getBounds(asGeoJSON=False):
    """
    Returns the bounds of the current map view, as a list in the format [west, south, east, north] in degrees.

    https://developers.google.com/earth-engine/api_docs#mapgetbounds

    Uses:
        >>> from ee_plugin import Map
        >>> bounds = Map.getBounds(True)
        >>> Map.addLayer(bounds, {}, 'bounds')
    """
    iface = get_iface()
    ex = iface.mapCanvas().extent()
    # return ex
    xmax = ex.xMaximum()
    ymax = ex.yMaximum()
    xmin = ex.xMinimum()
    ymin = ex.yMinimum()

    # return as [west, south, east, north]
    if not asGeoJSON:
        return [xmin, ymin, xmax, ymax]

    # return as geometry
    crs = iface.mapCanvas().mapSettings().destinationCrs().authid()

    return ee.Geometry.Rectangle([xmin, ymin, xmax, ymax], crs, False)


def getCenter():
    """
    Returns the coordinates at the center of the map.

    https://developers.google.com/earth-engine/api_docs#mapgetcenter

    Uses:
        >>> from ee_plugin import Map
        >>> center = Map.getCenter()
        >>> Map.addLayer(center, { 'color': 'red' }, 'center')
    """
    iface = get_iface()
    center = iface.mapCanvas().center()

    crs = iface.mapCanvas().mapSettings().destinationCrs().authid()

    return ee.Geometry.Point([center.x(), center.y()], crs)


def setCenter(lon, lat, zoom=None):
    """
    Centers the map view at the given coordinates with the given zoom level. If no zoom level is provided, it uses the most recent zoom level on the map.

    https://developers.google.com/earth-engine/api_docs#mapsetcenter

    Uses:
        >>> from ee_plugin import Map
        >>> Map.setCenter(lon, lat, zoom)
    """
    # wait 100 milliseconds while load the ee image
    loop = QEventLoop()
    QTimer.singleShot(100, loop.quit)
    for _ in range(10):  # Process events for 10 iterations
        QCoreApplication.processEvents()
        QThread.msleep(10)  ### center
    center_point_in = QgsPointXY(lon, lat)
    # convert coordinates
    crsSrc = QgsCoordinateReferenceSystem("EPSG:4326")
    crsDest = QgsCoordinateReferenceSystem(QgsProject.instance().crs())
    xform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())
    # forward transformation: src -> dest
    center_point = xform.transform(center_point_in)

    iface = get_iface()
    iface.mapCanvas().setCenter(center_point)

    ### zoom
    if zoom is not None:
        # transform the zoom level to scale
        scale_value = 591657550.5 / 2 ** (zoom - 1)
        iface.mapCanvas().zoomScale(scale_value)


def getScale():
    """
    Returns the approximate pixel scale of the current map view, in meters.

    https://developers.google.com/earth-engine/api_docs#mapgetscale

    Uses:
        >>> from ee_plugin import Map
        >>> print(Map.getScale())
    """
    iface = get_iface()
    return iface.mapCanvas().scale() / 1000


def getZoom():
    """
    Returns the current zoom level of the map.

    https://developers.google.com/earth-engine/api_docs#mapgetzoom

    Note that in QGIS zoom is a floating point number

    Uses:
        >>> from ee_plugin import Map
        >>> print(Map.getZoom())
    """

    # from https://gis.stackexchange.com/questions/268890/get-current-zoom-level-from-qgis-map-canvas
    iface = get_iface()
    scale = iface.mapCanvas().scale()
    dpi = iface.mainWindow().physicalDpiX()
    maxScalePerPixel = 156543.04
    inchesPerMeter = 39.37
    zoom = math.log((dpi * inchesPerMeter * maxScalePerPixel / scale), 2)

    return zoom


def setZoom(zoom):
    """
    Sets the zoom level of the map.

    https://developers.google.com/earth-engine/api_docs#mapsetzoom

    Uses:
        >>> from ee_plugin import Map
        >>> Map.setZoom(15)
    """

    center = getCenter()
    centerObject(ee.Feature(center), zoom)
