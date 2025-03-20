import os
import logging

from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProcessingProvider

from .algorithms import AddEEImageAlgorithm


logger = logging.getLogger(__name__)


class EEProcessingProvider(QgsProcessingProvider):
    def loadAlgorithms(self):
        self.addAlgorithm(AddEEImageAlgorithm())

    def id(self):
        return "ee"

    def name(self):
        return "GEE"

    def longName(self):
        return "Google Earth Engine Plugin"

    # TODO: fix icon not appearing in the processing toolbox
    def icon(self) -> QIcon:
        icon_path = self.svgIconPath()

        if not os.path.exists(icon_path):
            logging.error(f"[GEE Plugin] Icon file not found at: {icon_path}")
        else:
            logging.info(f"[GEE Plugin] Loading icon from: {icon_path}")

        return QIcon(icon_path)

    def svgIconPath(self) -> str:
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(plugin_dir, "..", "icons", "earth_engine.svg")
        icon_path = os.path.normpath(icon_path)

        return icon_path
