# -*- coding: utf-8 -*-
"""
Create and init the Earth Engine Qgis data provider
"""

import json

import ee
from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsDataProvider,
    QgsMessageLog,
    QgsProviderMetadata,
    QgsProviderRegistry,
    QgsRaster,
    QgsRasterDataProvider,
    QgsRasterIdentifyResult,
    QgsRasterInterface,
)
from qgis.PyQt.QtCore import QObject

from . import Map

BAND_TYPES = {
    "int8": Qgis.Int16,
    "int16": Qgis.Int16,
    "int32": Qgis.Int32,
    "int64": Qgis.Int32,
    "uint8": Qgis.UInt16,
    "uint16": Qgis.UInt16,
    "uint32": Qgis.UInt32,
    "byte": Qgis.Byte,
    "short": Qgis.Int16,
    "int": Qgis.Int16,
    "long": Qgis.Int32,
    "float": Qgis.Float32,
    "double": Qgis.Float64,
}


class EarthEngineRasterDataProvider(QgsRasterDataProvider):
    PARENT = QObject()

    def __init__(self, uri, providerOptions=None, flags=None, image=None):
        super().__init__()
        self.uri = uri
        self.providerOptions = providerOptions
        self.flags = flags
        self.ee_object = image
        self.ee_info = image.getInfo() if image else None

        # create WMS provider
        self.wms = QgsProviderRegistry.instance().createProvider(
            "wms", uri, providerOptions
        )
        assert self.wms, f"Failed to create WMS provider: {uri}"

    @classmethod
    def description(cls):
        return "Google Earth Engine Raster Data Provider"

    @classmethod
    def providerKey(cls):
        return "EE"

    @classmethod
    def createProvider(cls, uri, providerOptions, flags=None, image=None):
        # compatibility with Qgis < 3.16, ReadFlags only available since 3.16
        if Qgis.QGIS_VERSION_INT >= 31600:
            flags = QgsDataProvider.ReadFlags()
            provider = EarthEngineRasterDataProvider(uri, providerOptions, flags, image)
        else:
            provider = EarthEngineRasterDataProvider(uri, providerOptions, image=image)

        if image:
            provider.set_ee_object(image)

        return provider

    def crs(self):
        return QgsCoordinateReferenceSystem("EPSG:3857")

    def setDataSourceUri(self, uri):
        self.wms.setDataSourceUri(uri)

    def dataSourceUri(self, expandAuthConfig=None):
        return self.wms.dataSourceUri(expandAuthConfig)

    def dataComment(self):
        return self.wms.dataComment()

    def flags(self):
        return self.wms.flags()

    def temporalCapabilities(self):
        return self.wms.temporalCapabilities()

    def extent(self):
        return self.wms.extent()

    def isValid(self):
        return self.wms.isValid()

    def updateExtents(self):
        return self.wms.updateExtents()

    def setSubsetString(self, subset, updateFeatureCount=True):
        return self.wms.setSubsetString(subset, updateFeatureCount)

    def supportsSubsetString(self):
        return self.wms.supportsSubsetString()

    def subsetString(self):
        return self.wms.subsetString()

    def subLayers(self):
        return self.wms.subLayers()

    def subLayerStyles(self):
        return self.wms.subLayerStyles()

    def subLayerCount(self):
        return self.wms.subLayerCount()

    def setLayerOrder(self, layers):
        return self.wms.setLayerOrder(layers)

    def setSubLayerVisibility(self, name, vis):
        return self.wms.setSubLayerVisibility(name, vis)

    def name(self):
        return "EE"

    def fileVectorFilter(self):
        return self.wms.fileVectorFilters()

    def fileRasterFilter(self):
        return self.wms.fileRasterFilters()

    def reloadData(self):
        return self.wms.reloadData()

    def timestamp(self):
        return self.wms.timestamp()

    def dataTimestamp(self):
        return self.wms.dataTimestamp()

    def error(self):
        return self.wms.error()

    def invalidateConnections(self, connection):
        return self.wms.invalidateConnections(connection)

    def enterUpdateMode(self):
        return self.wms.enterUpdateMode()

    def leaveUpdateMode(self):
        return self.wms.leaveUpdateMode()

    def setListening(self, isListening):
        return self.wms.setListening(isListening)

    def renderInPreview(self, context):
        return self.wms.renderInPreview(context)

    def layerMetadata(self):
        return self.wms.layerMetadata()

    def writeLayerMetadata(self, metadata):
        return self.wms.writeLayerMetadata(metadata)

    def setTransformContext(self, transformContext):
        return self.wms.setTransformContext(transformContext)

    def reloadProviderData(self):
        return self.wms.reloadProviderData()

    def providerCapabilities(self):
        return self.wms.providerCapabilities()

    def fields(self):
        return self.wms.fields()

    def colorInterpretation(self, bandNo):
        return self.wms.colorInterpretation(bandNo)

    def reload(self):
        return self.wms.reload()

    def bandScale(self, bandNo):
        return self.wms.bandScale(bandNo)

    def bandOffset(self, bandNo):
        return self.wms.bandObbset(bandNo)

    def sourceHasNoDataValue(self, bandNo):
        return self.wms.sourceHasNoDataValue(bandNo)

    def useSourceNoDataValue(self, bandNo):
        return self.wms.useSourceNoDataValue(bandNo)

    def setUseSourceNoDataValue(self, bandNo, use):
        return self.wms.setUseSourceNoDataValue(bandNo, use)

    def sourceNoDataValue(self, bandNo):
        return self.wms.sourceNoDataValue(bandNo)

    def setUserNoDataValue(self, bandNo, noData):
        return self.wms.setUserNoDataValue(bandNo, noData)

    def userNoDataValues(self, bandNo):
        return self.wms.userNoDataValues(bandNo)

    def colorTable(self, bandNo):
        return self.wms.colorTable(bandNo)

    def supportsLegendGraphic(self):
        return self.wms.supportsLegendGraphic()

    def getLegendGraphic(self, scale=0, forceRefresh=False, visibleExtent=None):
        return self.wms.getLegendGraphic(scale, forceRefresh, visibleExtent)

    def getLegendGraphicFetcher(self, mapSettings):
        return self.wms.getLegendGraphicFetcher(mapSettings)

    def htmlMetadata(self):
        return json.dumps(self.ee_object.getInfo())

    def identify(
        self, point, format, boundingBox=None, width=None, height=None, dpi=None
    ):
        dataset_projection = self.ee_info["bands"][0]["crs"]
        point_ee = ee.Geometry.Point(
            [point.x(), point.y()], self.crs().authid()
        ).transform(dataset_projection)

        reducer = ee.Reducer.first()
        scale = Map.getScale()
        value = self.ee_object.reduceRegion(reducer, point_ee, scale).getInfo()
        band_indices = range(1, self.bandCount() + 1)
        band_names = [self.generateBandName(band_no) for band_no in band_indices]
        band_values = [value[band_name] for band_name in band_names]

        value = dict(zip(band_indices, band_values))
        result = QgsRasterIdentifyResult(QgsRaster.IdentifyFormatValue, value)

        return result

    def lastErrorTitle(self):
        return self.wms.lastErrorTitle()

    def lastError(self):
        return self.wms.lastError()

    def lastErrorFormat(self):
        return self.wms.lastErrorFormat()

    def isEditable(self):
        return self.wms.isEditable()

    def setEditable(self, enabled):
        return self.wms.setIsEditable(enabled)

    def remove(self):
        return self.wms.remove()

    def stepWidth(self):
        return self.wms.stepWidth()

    def stepHeight(self):
        return self.wms.stepHeight()

    def nativeResolutions(self):
        return self.wms.nativeResolutions()

    def ignoreExtents(self):
        return self.wms.ignoreExtents()

    def transformCoordinates(self, point, type):
        return self.wms.transformCoordinates(point, type)

    def enableProviderResampling(self, enable):
        return self.wms.enableProviderResampling(enable)

    def setZoomedInResamplingMethod(self, method):
        return self.wms.setZoomedInResamplingMethod(method)

    def setZoomedOutResamplingMethod(self, method):
        return self.wms.setZoomedOutResamplingMethod(method)

    def setMaxOversampling(self, factor):
        return self.wms.setMaxOversampling(factor)

    def writeNativeAttributeTable(self):
        return self.wms.writeNativeAttributeTable()

    def readNativeAttributeTable(self):
        return self.wms.readNativeAttributeTable()

    def getMapUrl(self):
        return self.wms.getMapUrl()

    def getFeatureInfoUrl(self):
        return self.wms.getFeatureInfoUrl()

    def getTileUrl(self):
        return self.wms.getTileUrl()

    def getLegendGraphicUrl(self):
        return self.wms.getLegendGraphicUrl()

    def clone(self):
        provider = EarthEngineRasterDataProvider(
            self.uri, self.providerOptions, self.flags, self.ee_object
        )
        provider.wms.setDataSourceUri(self.wms.dataSourceUri())
        provider.set_ee_object(self.ee_object)
        provider.setParent(EarthEngineRasterDataProvider.PARENT)

        return provider

    def capabilities(self):
        caps = (
            QgsRasterInterface.Size
            | QgsRasterInterface.Identify
            | QgsRasterInterface.IdentifyValue
        )

        if Qgis.versionInt() >= 33800:
            return Qgis.RasterInterfaceCapabilities(caps)
        else:
            return QgsRasterDataProvider.ProviderCapabilities(caps)

    def dataType(self, band_no):
        return self.wms.dataType(band_no)

    def sourceDataType(self, band_no):
        return self.wms.sourceDataType(band_no)

    def bandCount(self):
        if self.ee_object:
            return len(self.ee_info["bands"])
        else:
            return 1  # fall back to default if ee_object is not set

    def generateBandName(self, band_no):
        return self.ee_info["bands"][band_no - 1]["id"]

    def xBlockSize(self):
        return self.wms.xBlockSize()

    def yBlockSize(self):
        return self.wms.yBlockSize()

    def xSize(self):
        return self.wms.xSize()

    def ySize(self):
        return self.wms.ySize()

    def colorInterpretationName(self, bandNumber):
        return self.wms.colorInterpretationName(bandNumber)

    def block(self, bandNo, extent, width, height, feedback=None):
        return self.wms.block(bandNo, extent, width, height, feedback)

    def setInput(self, input):
        return self.wms.setInput(input)

    def input(self):
        return self.wms.input()

    def on(self):
        return self.wms.on()

    def setOn(self, on):
        return self.wms.setOn(on)

    def sourceInput(self):
        return self.wms.sourceInput()

    def set_ee_object(self, ee_object):
        self.ee_object = ee_object
        self.ee_info = ee_object.getInfo()


def register_data_provider():
    metadata = QgsProviderMetadata(
        EarthEngineRasterDataProvider.providerKey(),
        EarthEngineRasterDataProvider.description(),
        EarthEngineRasterDataProvider.createProvider,
    )
    registry = QgsProviderRegistry.instance()
    registry.registerProvider(metadata)
    QgsMessageLog.logMessage("EE provider registered")
