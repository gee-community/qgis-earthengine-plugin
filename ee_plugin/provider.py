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
        super().__init__(uri, providerOptions, flags)
        self.providerOptions = providerOptions
        self.flags = flags
        self.ee_object = image
        self.ee_info = image.getInfo() if image else None

    @classmethod
    def description(cls):
        return "Google Earth Engine Raster Data Provider"

    @classmethod
    def providerKey(cls):
        return "EE"

    @classmethod
    def createProvider(
        cls, uri, providerOptions, flags=None, image=None
    ) -> "EarthEngineRasterDataProvider":
        # compatibility with Qgis < 3.16, ReadFlags only available since 3.16
        if Qgis.QGIS_VERSION_INT >= 31600:
            flags = QgsDataProvider.ReadFlags()
            return EarthEngineRasterDataProvider(uri, providerOptions, flags, image)
        else:
            return EarthEngineRasterDataProvider(uri, providerOptions, image=image)

    def crs(self):
        return QgsCoordinateReferenceSystem("EPSG:3857")

    def name(self):
        return self.providerKey()

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

    def clone(self):
        provider = EarthEngineRasterDataProvider(
            self.uri, self.providerOptions, self.flags, self.ee_object
        )
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

    def bandCount(self):
        if self.ee_object:
            return len(self.ee_info["bands"])
        else:
            return 1  # fall back to default if ee_object is not set

    def generateBandName(self, band_no):
        return self.ee_info["bands"][band_no - 1]["id"]

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
