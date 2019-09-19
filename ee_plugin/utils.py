# -*- coding: utf-8 -*-
"""
Utils functions GEE
"""

from qgis.core import QgsRasterLayer, QgsProject
from qgis.utils import iface

import ee

def get_image_url(image):
    map_id = ee.data.getMapId({'image': image}) 
    url = map_id['tile_fetcher'].url_format
    return url

def update_ee_layer_properties(layer, image, visibility, opacity):
    layer.setCustomProperty('ee-layer', True)

    if not (opacity is None):
        layer.renderer().setOpacity(opacity)

    # serialize EE code
    ee_script = image.serialize()
    layer.setCustomProperty('ee-script', ee_script)

def add_ee_image_layer(image, name, visibility, opacity):
    url = "type=xyz&url=" + get_image_url(image)
    layer = QgsRasterLayer(url, name, "wms")
    update_ee_layer_properties(layer, image, visibility, opacity)
    QgsProject.instance().addMapLayer(layer)

    if not (visibility is None):
        QgsProject.instance().layerTreeRoot().findLayer(layer.id()).setItemVisibilityChecked(visibility)

def update_ee_image_layer(image, layer, visibility=True, opacity=1.0):
    url = "type=xyz&url=" + get_image_url(image)
    layer.dataProvider().setDataSourceUri(url)
    layer.dataProvider().reloadData()
    update_ee_layer_properties(layer, image, visibility, opacity)
    layer.triggerRepaint()
    layer.reload()
    iface.mapCanvas().refresh()
    
    item = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
    if not (visibility is None):
        item.setItemVisibilityChecked(visibility)
    
def get_layer_by_name(name):
    layers = QgsProject.instance().mapLayers().values()    
    
    for l in layers:
        if(l.name() == name):
            return l
            
    return None

def add_or_update_ee_image_layer(image, name, visibility, opacity):
    layer = get_layer_by_name(name)

    if layer: 
        if not layer.customProperty('ee-layer'):
            raise Exception('Layer is not an EE layer: ' + name)
    
        update_ee_image_layer(image, layer, visibility, opacity)
    else:
        add_ee_image_layer(image, name, visibility, opacity)

def add_ee_catalog_image(name, asset_name, vis_props, collection_props):
    image = None
    
    if collection_props:
        raise Exception('Not supported yet')
    else:
        image = ee.Image(asset_name).visualize(vis_props)

    add_or_update_ee_image_layer(image, name)

