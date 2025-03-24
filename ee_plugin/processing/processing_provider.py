from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProcessingProvider

from .add_ee_image import AddEEImageAlgorithm
from .add_image_collection import AddImageCollectionAlgorithm
from .export_geotiff import ExportGeoTIFFAlgorithm


class EEProcessingProvider(QgsProcessingProvider):
    def __init__(self, icon: QIcon, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._icon = icon

    def loadAlgorithms(self):
        self.addAlgorithm(AddEEImageAlgorithm())
        self.addAlgorithm(AddImageCollectionAlgorithm())
        self.addAlgorithm(ExportGeoTIFFAlgorithm())

    def id(self):
        return "ee"

    def name(self):
        return "GEE"

    def longName(self):
        return "Google Earth Engine Plugin"

    def icon(self) -> QIcon:
        return self._icon
