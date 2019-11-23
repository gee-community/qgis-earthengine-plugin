# -*- coding: utf-8 -*-
"""
functions to use GEE within Qgis python script
"""
import math
import json
import ee

from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, Qgis, QgsProject, QgsPointXY, QgsRectangle
from qgis.utils import iface

import ee_plugin.utils


def addLayer(image: ee.Image, visParams=None, name=None, shown=True, opacity=1.0):
    """
        Adds a given EE object to the map as a layer.

        https://developers.google.com/earth-engine/api_docs#map.addlayer

        Uses:
            >>> from ee_plugin import Map
            >>> Map.addLayer(.....)
    """

    if not isinstance(image, ee.Image) and not isinstance(image, ee.FeatureCollection) and not isinstance(image, ee.Feature) and not isinstance(image, ee.Geometry):
        err_str = "\n\nThe image argument in 'addLayer' function must be an instace of one of ee.Image, ee.Geometry, ee.Feature or ee.FeatureCollection."
        raise AttributeError(err_str)

    if isinstance(image, ee.Geometry) or isinstance(image, ee.Feature) or isinstance(image, ee.FeatureCollection):
        features = ee.FeatureCollection(image)

        color = '000000'

        if visParams and 'color' in visParams:
            color = visParams['color']

        image = features.style(**{'color': color})

    else:
        if isinstance(image, ee.Image) and visParams:
            image = image.visualize(**visParams)

    if name is None:
        # extract name from id
        try:
            name = json.loads(image.id().serialize())[
                "scope"][0][1]["arguments"]["id"]
        except:
            name = "untitled"

    ee_plugin.utils.add_or_update_ee_image_layer(image, name, shown, opacity)


def centerObject(feature, zoom=None):
    """
        Centers the map view on a given object.

        https://developers.google.com/earth-engine/api_docs#map.centerobject

        Uses:
            >>> from ee_plugin import Map
            >>> Map.centerObject(feature)
    """
    if not zoom:
        # make sure our geometry is in geo
        rect = feature.geometry().transform(ee.Projection('EPSG:4326'), 1)

        # get coordinates
        coords = rect.bounds().getInfo()['coordinates'][0]
        xmin = coords[0][0]
        ymin = coords[0][1]
        xmax = coords[2][0]
        ymax = coords[2][1]

        # construct QGIS geometry
        rect = QgsRectangle(xmin, ymin, xmax, ymax)

        # transform rect to a crs used by current project
        crs_src = QgsCoordinateReferenceSystem(4326)
        crs_dst = QgsCoordinateReferenceSystem(QgsProject.instance().crs())
        xform = QgsCoordinateTransform(crs_src, crs_dst, QgsProject.instance())
        rect_proj = xform.transform(rect)

        # center geometry
        iface.mapCanvas().zoomToFeatureExtent(rect_proj)
    else:
        # set map center to feature centroid at a specified zoom
        center = feature.geometry().centroid().coordinates().getInfo()
        setCenter(center[0], center[1], zoom)


def getBounds(asGeoJSON=False):
    """
        Returns the bounds of the current map view, as a list in the format [west, south, east, north] in degrees.

        https://developers.google.com/earth-engine/api_docs#map.getbounds

        Uses:
            >>> from ee_plugin import Map
            >>> bounds = Map.getBounds(True)
            >>> Map.addLayer(bounds, {}, 'bounds')
    """
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

        https://developers.google.com/earth-engine/api_docs#map.getcenter

        Uses:
            >>> from ee_plugin import Map
            >>> center = Map.getCenter()
            >>> Map.addLayer(center, { 'color': 'red' }, 'center')
    """
    center = iface.mapCanvas().center()

    crs = iface.mapCanvas().mapSettings().destinationCrs().authid()

    return ee.Geometry.Point([center.x(), center.y()], crs)


def setCenter(lon, lat, zoom=None):
    """
        Centers the map view at the given coordinates with the given zoom level. If no zoom level is provided, it uses the most recent zoom level on the map.

        https://developers.google.com/earth-engine/api_docs#map.setcenter

        Uses:
            >>> from ee_plugin import Map
            >>> Map.setCenter(lon, lat, zoom)
    """

    ### center
    center_point_in = QgsPointXY(lon, lat)
    # convert coordinates
    crsSrc = QgsCoordinateReferenceSystem(4326)  # WGS84
    crsDest = QgsCoordinateReferenceSystem(QgsProject.instance().crs())
    xform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())
    # forward transformation: src -> dest
    center_point = xform.transform(center_point_in)
    iface.mapCanvas().setCenter(center_point)

    ### zoom
    if zoom is not None:
        # transform the zoom level to scale
        scale_value = 591657550.5 / 2 ** (zoom - 1)
        iface.mapCanvas().zoomScale(scale_value)


def getScale():
    """
        Returns the approximate pixel scale of the current map view, in meters.

        https://developers.google.com/earth-engine/api_docs#map.getscale

        Uses:
            >>> from ee_plugin import Map
            >>> print(Map.getScale())
    """

    return iface.mapCanvas().scale() / 1000


def getZoom():
    """
        Returns the current zoom level of the map.

        https://developers.google.com/earth-engine/api_docs#map.getzoom, note that in QGIS zoom is a floating point number

        Uses:
            >>> from ee_plugin import Map
            >>> print(Map.getZoom())
    """

    # from https://gis.stackexchange.com/questions/268890/get-current-zoom-level-from-qgis-map-canvas
    scale = iface.mapCanvas().scale()
    dpi = iface.mainWindow().physicalDpiX()
    maxScalePerPixel = 156543.04
    inchesPerMeter = 39.37
    zoom = math.log((dpi * inchesPerMeter * maxScalePerPixel / scale), 2)

    return zoom


def setZoom(zoom):
    """
        Sets the zoom level of the map.

        https://developers.google.com/earth-engine/api_docs#map.setzoom

        Uses:
            >>> from ee_plugin import Map
            >>> Map.setZoom(15)
    """

    center = getCenter()
    centerObject(ee.Feature(center), zoom)
