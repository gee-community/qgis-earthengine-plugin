# -*- coding: utf-8 -*-
"""
functions to use GEE within Qgis python script
"""

import ee_plugin.utils

def addLayer(image, vis=None, name=None, visible=None, opacity=None):
    """
        Mimique addLayer GEE function

        Uses:
            >>> from ee_plugin import Map
            >>> Map.addLayer(.....)
    """
    if vis:
        image = image.visualize(**vis)
        
    if not name:
        name = 'untitled'

    if not opacity:
        opacity = 1.0

    if not (visible is None):
        visible = True
    
    ee_plugin.utils.add_or_update_ee_image_layer(image, name, visible, opacity)
