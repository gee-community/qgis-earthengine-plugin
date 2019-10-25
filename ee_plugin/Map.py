# -*- coding: utf-8 -*-
"""
functions to use GEE within Qgis python script
"""
import ee

import ee_plugin.utils


def addLayer(image, vis_props=None, name='untitled', visibility=True, opacity=1.0):
    """
        Mimique addLayer GEE function

        Uses:
            >>> from ee_plugin import Map
            >>> Map.addLayer(.....)
    """

    if not isinstance(image, ee.Image):
        err_str = "\n\nThe image argument in 'addLayer' function must be a 'ee.Image' instance."
        raise AttributeError(err_str)

    if vis_props:
        image = image.visualize(**vis_props)

    ee_plugin.utils.add_or_update_ee_image_layer(image, name, visibility, opacity)
