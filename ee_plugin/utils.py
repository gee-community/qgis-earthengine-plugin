# -*- coding: utf-8 -*-
"""
Utils functions GEE
"""

from qgis.core import QgsRasterLayer, QgsProject
from qgis.utils import iface

import ee


def get_ee_image_url(image):
    map_id = ee.data.getMapId({'image': image}) 
    url = map_id['tile_fetcher'].url_format
    return url


def update_ee_layer_properties(layer, image, shown, opacity):
    layer.setCustomProperty('ee-layer', True)

    if not (opacity is None):
        layer.renderer().setOpacity(opacity)

    # serialize EE code
    ee_script = image.serialize()
    layer.setCustomProperty('ee-script', ee_script)


def add_ee_image_layer(image, name, shown, opacity):
    url = "type=xyz&url=" + get_ee_image_url(image)
    layer = QgsRasterLayer(url, name, "wms")
    update_ee_layer_properties(layer, image, shown, opacity)
    QgsProject.instance().addMapLayer(layer)

    if not (shown is None):
        QgsProject.instance().layerTreeRoot().findLayer(layer.id()).setItemVisibilityChecked(shown)


def update_ee_image_layer(image, layer, shown=True, opacity=1.0):
    url = "type=xyz&url=" + get_ee_image_url(image)
    layer.dataProvider().setDataSourceUri(url)
    layer.dataProvider().reloadData()
    update_ee_layer_properties(layer, image, shown, opacity)
    layer.triggerRepaint()
    layer.reload()
    iface.mapCanvas().refresh()
    
    item = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
    if not (shown is None):
        item.setItemVisibilityChecked(shown)


def get_layer_by_name(name):
    layers = QgsProject.instance().mapLayers().values()    
    
    for l in layers:
        if l.name() == name:
            return l
            
    return None


def add_or_update_ee_image_layer(image, name, shown=True, opacity=1.0):
    layer = get_layer_by_name(name)

    if layer: 
        if not layer.customProperty('ee-layer'):
            raise Exception('Layer is not an EE layer: ' + name)
    
        update_ee_image_layer(image, layer, shown, opacity)
    else:
        add_ee_image_layer(image, name, shown, opacity)


def add_ee_catalog_image(name, asset_name, visParams, collection_props):
    image = None
    
    if collection_props:
        raise Exception('Not supported yet')
    else:
        image = ee.Image(asset_name).visualize(visParams)

    add_or_update_ee_image_layer(image, name)

