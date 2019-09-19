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

def add_ee_image_layer(image, name):
    url = get_image_url(image)

    layer = QgsRasterLayer("type=xyz&url=" + url, name, "wms")
    layer.setCustomProperty('ee-layer', True)

    # serialize EE code
    ee_script = image.serialize()
    layer.setCustomProperty('ee-script', ee_script)

    QgsProject.instance().addMapLayer(layer)

def update_ee_image_layer(image, layer):
    url = "type=xyz&url=" + get_image_url(image)
    
    layer.dataProvider().setDataSourceUri(url)
    layer.dataProvider().reloadData()
    layer.triggerRepaint()
    layer.reload()
    
    iface.mapCanvas().refresh()
    
def get_layer_by_name(name):
    layers = QgsProject.instance().mapLayers().values()    
    
    for l in layers:
        if(l.name() == name):
            return l
            
    return None

def add_or_update_ee_image_layer(image, name):
    layer = get_layer_by_name(name)

    if layer: 
        if not layer.customProperty('ee-layer'):
            raise Exception('Layer is not an EE layer: ' + name)
    
        update_ee_image_layer(image, layer)
    else:
        add_ee_image_layer(image, name)


def add_ee_catalog_image(name, asset_name, vis_props, collection_props):
    image = None
    
    if collection_props:
        raise Exception('Not supported yet')
    else:
        image = ee.Image(asset_name).visualize(vis_props)

    add_or_update_ee_image_layer(image, name)

    # set custom property ee_catalog_image = Truw

def add_SRTM_layer():
    palette = ['543005', '8c510a', 'bf812d', 'dfc27d', 'f6e8c3', 'f5f5f5', 'c7eae5', '80cdc1', '35978f', '01665e', '003c30']
    palette.reverse()
    
    image = ee.Image('USGS/SRTMGL1_003').unitScale(0, 5000) \
        .visualize(**{ 'palette': palette})
        
    add_or_update_ee_image_layer(image, 'dem')