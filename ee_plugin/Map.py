# -*- coding: utf-8 -*-
"""
functions to use GEE within Qgis python script
"""
import json
import ee

from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, Qgis, QgsProject, QgsPointXY
from qgis.utils import iface

import ee_plugin.utils

def addLayer(image: ee.Image, visParams=None, name=None, shown=True, opacity=1.0):
    """
        Mimique addLayer GEE function

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

        image = features.style(**{ 'color': color })

    else:
        if isinstance(image, ee.Image) and visParams:
            image = image.visualize(**visParams)

    if name is None:
        # extract name from id
        try:
            name = json.loads(image.id().serialize())["scope"][0][1]["arguments"]["id"]
        except:
            name = "untitled"

    ee_plugin.utils.add_or_update_ee_image_layer(image, name, shown, opacity)


def setCenter(lon, lat, zoom=None):
    """
        Mimique setCenter GEE function

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
