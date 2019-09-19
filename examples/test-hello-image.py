# -*- coding: utf-8 -*-

from qgis.core import QgsRasterLayer, QgsProject
from qgis.utils import iface

import ee
ee.Initialize()

def get_image_url(image):
    map_id = ee.data.getMapId({'image': image}) 
    url = map_id['tile_fetcher'].url_format
    return url

def add_ee_xyz_tile_layer(url, name):
    layer = QgsRasterLayer("type=xyz&url=" + url, name, "wms")
    layer.setCustomProperty('ee-layer', True)
    QgsProject.instance().addMapLayer(layer)

def add_ee_image_layer(image, name):
    url = get_image_url(image)
    add_ee_xyz_tile_layer(url, name)

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


image = ee.Image('USGS/SRTMGL1_003').unitScale(0, 5000) \
    .visualize(**{ 'palette': ['blue', 'red']})
    
add_or_update_ee_image_layer(image, 'dem')

