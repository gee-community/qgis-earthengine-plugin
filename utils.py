# -*- coding: utf-8 -*-
"""
Utils functions GEE
"""
import json
import qgis.core
from qgis.core import QgsRasterLayer, QgsProject, QgsRasterDataProvider, QgsRasterIdentifyResult, QgsProviderRegistry, QgsProviderMetadata, QgsMessageLog
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, Qgis, QgsProject, QgsRaster, QgsRasterInterface, QgsSettings
from qgis.core import QgsPointXY, QgsRectangle
from qgis.utils import iface
import qgis
import ee

from ee_plugin import Map

def get_ee_image_url(image):
    map_id = ee.data.getMapId({'image': image})
    url = map_id['tile_fetcher'].url_format
    return url


def update_ee_layer_properties(layer, eeObject, visParams, shown, opacity):
    layer.setCustomProperty('ee-layer', True)

    if not (opacity is None):
        renderer = layer.renderer()
        if renderer:
            renderer.setOpacity(opacity)

    # serialize EE code
    ee_object = eeObject.serialize()
    ee_object_vis = json.dumps(visParams)
    layer.setCustomProperty('ee-object', ee_object)
    layer.setCustomProperty('ee-object-vis', ee_object_vis)

    # update EE script in provider 
    layer.dataProvider().ee_object = eeObject


def add_ee_image_layer(image, name, shown, opacity):
    check_version()

    url = "type=xyz&url=" + get_ee_image_url(image)
    layer = QgsRasterLayer(url, name, "EE")

    if layer:
        provider = layer.dataProvider()
        QgsMessageLog.logMessage('Created layer with provider %s' % (type(provider).__name__, ), 'Earth Engine')
    else:
        QgsMessageLog.logMessage('Layer not created', 'Earth Engine')
    
    QgsProject.instance().addMapLayer(layer)

    if not (shown is None):
        QgsProject.instance().layerTreeRoot().findLayer(
            layer.id()).setItemVisibilityChecked(shown)

    return layer


def update_ee_image_layer(image, layer, shown=True, opacity=1.0):
    check_version()

    url = "type=xyz&url=" + get_ee_image_url(image)

    provider = layer.dataProvider()
    msg = 'Updating layer with provider %s' % (type(provider).__name__, )
    QgsMessageLog.logMessage(msg, 'Earth Engine')
    
    provider.setDataSourceUri(url)
    provider.reloadData()
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
    class EarthEngineRasterDateProvider(QgsRasterDataProvider):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            # create WMS provider
            self.wms = qgis.core.QgsProviderRegistry.instance().createProvider('wms', *args)
            # print('wms', self.wms)

        @classmethod
        def description(cls):
            return 'Google Earth Engine Raster Data Provider'
        
        @classmethod
        def providerKey(cls):
            return 'EE'

        @classmethod
        def createProvider(cls, uri, providerOptions):
            return EarthEngineRasterDateProvider(uri, providerOptions)

        def capabilities(self):
            caps = QgsRasterInterface.Size | QgsRasterInterface.Identify | QgsRasterInterface.IdentifyHtml
            return QgsRasterDataProvider.ProviderCapabilities(caps)

        def extent(self):
            return self.wms.extent()

        def crs(self):
            return self.wms.crs()

        def clone(self):
            return self.wms.clone()

        def setDataSourceUri(self, uri):
            return self.wms.setDataSourceUri(uri)

        def reloadData(self):
            return self.wms.reloadData()

        def bandCount(self):
            return self.wms.bandCount()

        def dataType(self, band_no):
            return self.wms.dataType(band_no)
        
        def identify(self, point, format, boundingBox, width, height, dpi):
            # THIS IS NOT A DRAWN RECT BUT A FULL SCREEN RECT?
            # rect = geom_to_geo(boundingBox)
            # rect = ee.Geometry.Rectangle([rect.xMinimum(), rect.yMinimum(), rect.xMaximum(), rect.yMaximum()], 'EPSG:4326', False)
            # print(width, height, dpi)

            point = geom_to_geo(point) 

            point_ee = ee.Geometry.Point([point.x(), point.y()])

            scale = Map.getScale()
            value = self.ee_object.reduceRegion(ee.Reducer.first(), point_ee, scale).getInfo()

            settings = QgsSettings()

            color_text = settings.value("pythonConsole/defaultFontColor").name()
            color_bg = settings.value("pythonConsole/paperBackgroundColor").name()

            style = '''
            <style>
                .container {{ overflow: hidden; background-color: {0}; margin: -8px; padding: 0; min-height: 100px }}
            </style>
            '''

            html = style + '''
            <div class="container">
                <table style="font-family: monospace; color: {1}">
           '''

            for key in value.keys():
                row = '''
                    <tr>
                        <td>{0}</td>
                        <td>{1}</td>
                    </tr>
                '''

                row = row.format(key, str(value[key]))

                html += row
            
            html += '</table></div>'
            html = html.format(color_bg, color_text)

            import matplotlib.pyplot as plt
            import base64
            from io import BytesIO
            
            plt.style.use('dark_background')
            fig = plt.figure(figsize=(5,2.5))
            ax = plt.gca()
            ax.set_facecolor(color_bg)
            fig.set_facecolor(color_bg)
            plt.scatter([1, 10], [5, 9])
            tmpfile = BytesIO()
            fig.savefig(tmpfile, format='png', facecolor=fig.get_facecolor())
            encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
            html_figure = style + '<div class="container"><img src=\'data:image/png;base64,{1}\'></div>'
            html_figure = html_figure.format(color_bg, encoded)
            
            value = { 1: html, 2: html_figure }

            # IdentifyFormatHtml
            result = QgsRasterIdentifyResult(QgsRaster.IdentifyFormatHtml, value) 

            return result

        def isValid(self):
            return self.wms.isValid()

        def name(self):
            return 'Google Earth Engine Raster Data Provider'

    metadata = QgsProviderMetadata(
        EarthEngineRasterDateProvider.providerKey(), 
        EarthEngineRasterDateProvider.description(), 
        EarthEngineRasterDateProvider.createProvider)
    registry = qgis.core.QgsProviderRegistry.instance()
    registry.registerProvider(metadata)
    QgsMessageLog.logMessage('EE provider registered')


def add_or_update_ee_layer(eeObject, visParams, name, shown, opacity):
    image = None

    if not isinstance(eeObject, ee.Image) and not isinstance(eeObject, ee.FeatureCollection) and not isinstance(eeObject, ee.Feature) and not isinstance(eeObject, ee.Geometry):
        err_str = "\n\nThe image argument in 'addLayer' function must be an instace of one of ee.Image, ee.Geometry, ee.Feature or ee.FeatureCollection."
        raise AttributeError(err_str)

    if isinstance(eeObject, ee.Geometry) or isinstance(eeObject, ee.Feature) or isinstance(eeObject, ee.FeatureCollection):
        features = ee.FeatureCollection(eeObject)

        color = '000000'

        if 'color' in visParams:
            color = visParams['color']

        image_fill = features.style(**{'fillColor': color}).updateMask(ee.Image.constant(0.5))
        image_outline = features.style(**{'color': color, 'fillColor': '00000000', 'width': 2})

        image = image_fill.blend(image_outline)

    else:
        if isinstance(eeObject, ee.Image):
            image = eeObject.visualize(**visParams)

    if name is None:
        # extract name from id
        try:
            name = json.loads(eeObject.id().serialize())[
                "scope"][0][1]["arguments"]["id"]
        except:
            name = "untitled"

    layer = add_or_update_ee_image_layer(image, name, shown, opacity)

    update_ee_layer_properties(layer, eeObject, visParams, shown, opacity)

def add_or_update_ee_image_layer(image, name, shown=True, opacity=1.0):
    layer = get_layer_by_name(name)

    if layer:
        if not layer.customProperty('ee-layer'):
            raise Exception('Layer is not an EE layer: ' + name)

        update_ee_image_layer(image, layer, shown, opacity)
    else:
        layer = add_ee_image_layer(image, name, shown, opacity)

    return layer


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

def geom_to_geo(geom):
    print(geom)
    crs_src = QgsCoordinateReferenceSystem(QgsProject.instance().crs())
    crs_dst = QgsCoordinateReferenceSystem(4326)
    proj2geo = QgsCoordinateTransform(crs_src, crs_dst, QgsProject.instance())
    
    if isinstance(geom, QgsPointXY):
        return proj2geo.transform(geom)
    elif isinstance(geom, QgsRectangle):
        return proj2geo.transformBoundingBox(geom)
    else: 
        return geom.transform(proj2geo)
