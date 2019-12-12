# -*- coding: utf-8 -*-
"""
Utils functions GEE
"""
import qgis.core
from qgis.core import QgsRasterLayer, QgsProject, QgsRasterDataProvider, QgsRasterIdentifyResult, QgsProviderRegistry, QgsProviderMetadata, QgsMessageLog
from qgis.utils import iface
import qgis

import ee

def get_ee_image_url(image):
    map_id = ee.data.getMapId({'image': image})
    url = map_id['tile_fetcher'].url_format
    return url


def update_ee_layer_properties(layer, image, shown, opacity):
    layer.setCustomProperty('ee-layer', True)

    if not (opacity is None):
        renderer = layer.renderer()
        if renderer:
            renderer.setOpacity(opacity)

    # serialize EE code
    ee_script = image.serialize()
    layer.setCustomProperty('ee-script', ee_script)


def add_ee_image_layer(image, name, shown, opacity):
    check_version()


    url = "type=xyz&url=" + get_ee_image_url(image)
    layer = QgsRasterLayer(url, name, "EE")

    if layer:
        provider = layer.dataProvider()
        QgsMessageLog.logMessage('Created layer with provider %s' % (type(provider).__name__, ), 'ee')
    else:
        QgsMessageLog.logMessage('Layer not created', 'ee')
    
    update_ee_layer_properties(layer, image, shown, opacity)
    QgsProject.instance().addMapLayer(layer)

    if not (shown is None):
        QgsProject.instance().layerTreeRoot().findLayer(
            layer.id()).setItemVisibilityChecked(shown)


def update_ee_image_layer(image, layer, shown=True, opacity=1.0):
    check_version()

    url = "type=xyz&url=" + get_ee_image_url(image)

    provider = layer.dataProvider()
    msg = 'Updating layer with provider %s' % (type(provider).__name__, )
    QgsMessageLog.logMessage(msg, 'ee')
    
    provider.setDataSourceUri(url)
    provider.reloadData()
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


def register_data_provider():
    class EEProvider(QgsRasterDataProvider):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        @classmethod
        def description(cls):
            return 'Earth Engine Provider'
        @classmethod
        def providerKey(cls):
            return 'EE'
        @classmethod
        def createProvider(cls, uri, providerOptions):
            return EEProvider(uri, providerOptions)

        def dataType(self, band_no):
            # can't find qgis.core.ARGB32
            return 12
        
        def identify(self, *args, **kwargs):
            print('identify', *args, **kwargs)
            result = QgsRasterIdentifyResult()
            return result

        def isValid(self):
            return True

        def name(self):
            return 'EE Provider'

    metadata = QgsProviderMetadata(EEProvider.providerKey(), EEProvider.description(), EEProvider.createProvider)
    registry = qgis.core.QgsProviderRegistry.instance()
    registry.registerProvider(metadata)
    


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

def check_version():
    # check if we have the latest version only once plugin is used, not once it is loaded
    qgis.utils.plugins['ee_plugin'].check_version()



    


