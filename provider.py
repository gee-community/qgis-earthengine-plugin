import json

import qgis
from qgis.core import QgsRasterDataProvider, QgsRasterIdentifyResult, QgsProviderRegistry
from qgis.core import QgsRasterLayer, QgsProviderRegistry, QgsProviderMetadata
from qgis.core import QgsMessageLog
from qgis.core import Qgis, QgsRaster, QgsRasterInterface, QgsSettings

import ee

from ee_plugin import utils

BAND_TYPES = {
    'int8': Qgis.Int16,
    'int16': Qgis.Int16,
    'int32': Qgis.Int32,
    'int64': Qgis.Int32,
    'uint8': Qgis.UInt16,
    'uint16': Qgis.UInt16,
    'uint32': Qgis.UInt32,
    'byte': Qgis.Byte,
    'short': Qgis.Int16,
    'int': Qgis.Int16,
    'long': Qgis.Int32,
    'float': Qgis.Float32,
    'double': Qgis.Float64
}


class EarthEngineRasterDataProvider(QgsRasterDataProvider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # create WMS provider
        self.wms = qgis.core.QgsProviderRegistry.instance().createProvider('wms', *args)

        self.ee_object = None

    @classmethod
    def description(cls):
        return 'Google Earth Engine Raster Data Provider'

    @classmethod
    def providerKey(cls):
        return 'EE'

    @classmethod
    def createProvider(cls, uri, providerOptions):
        return EarthEngineRasterDataProvider(uri, providerOptions)

    def set_ee_object(self, ee_object):
        self.ee_object = ee_object
        self.ee_info = ee_object.getInfo()

    def capabilities(self):
        caps = QgsRasterInterface.Size | QgsRasterInterface.Identify | QgsRasterInterface.IdentifyValue
        return QgsRasterDataProvider.ProviderCapabilities(caps)

    def name(self):
        return self.wms.name()

    def isValid(self):
        return self.wms.isValid()

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

    def htmlMetadata(self):
        return json.dumps(self.ee_object.getInfo())

    def bandCount(self):
        if not self.ee_object:
            return 1 # fall back to default if ee_object is not set

        return len(self.ee_info['bands'])

    def dataType(self, band_no):
        if not self.ee_object:
            return self.wms.dataType(band_no)

        return self.sourceDataType(band_no)

    def generateBandName(self, band_no):
        return self.ee_info['bands'][band_no - 1]['id']

    def sourceDataType(self, band_no):
        return BAND_TYPES[self.ee_info['bands'][band_no - 1]['data_type']['precision']]

    def identify(self, point, format, boundingBox=None, width=None, height=None, dpi=None):
        # TODO: speed-up, extend this to maintain cache of visible image, update cache on-the-fly when needed
        from ee_plugin import Map

        point = utils.geom_to_geo(point)

        point_ee = ee.Geometry.Point([point.x(), point.y()])

        scale = Map.getScale()

        value = self.ee_object.reduceRegion(
            ee.Reducer.first(), point_ee, scale).getInfo()

        band_indices = range(1, self.bandCount() + 1)
        band_names = [self.generateBandName(
            band_no) for band_no in band_indices]
        band_values = [value[band_name] for band_name in band_names]

        value = dict(zip(band_indices, band_values))

        result = QgsRasterIdentifyResult(QgsRaster.IdentifyFormatValue, value)

        return result


def register_data_provider():
    metadata = QgsProviderMetadata(
        EarthEngineRasterDataProvider.providerKey(),
        EarthEngineRasterDataProvider.description(),
        EarthEngineRasterDataProvider.createProvider)
    registry = qgis.core.QgsProviderRegistry.instance()
    registry.registerProvider(metadata)
    QgsMessageLog.logMessage('EE provider registered')
