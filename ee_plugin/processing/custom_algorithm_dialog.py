import typing
from abc import abstractmethod

from datetime import datetime
from typing import Optional, Dict

from osgeo import gdal
import processing
from qgis.core import (
    Qgis,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingAlgorithm,
)
from qgis.PyQt.QtCore import Qt, QT_VERSION_STR
from qgis.PyQt.QtWidgets import QWidget
from qgis import gui

from ..logging import local_context


class BaseAlgorithmDialog(gui.QgsProcessingAlgorithmDialogBase):
    def __init__(
        self,
        algorithm: QgsProcessingAlgorithm,
        parent: Optional[QWidget] = None,
        title: Optional[str] = None,
    ):
        super().__init__(
            parent,
            flags=Qt.WindowFlags(),
            mode=gui.QgsProcessingAlgorithmDialogBase.DialogMode.Single,
        )
        self.setAlgorithm(algorithm)
        self.setModal(True)
        self.setWindowTitle(title or algorithm.displayName())

        # Hook up layout
        self.panel = gui.QgsPanelWidget()
        layout = self.buildDialog()
        self.panel.setLayout(layout)
        self.setMainWidget(self.panel)

        self.cancelButton().clicked.connect(self.reject)

    @abstractmethod
    def buildDialog(self) -> QWidget:
        """
        Build the dialog layout."
        """
        pass

    @abstractmethod
    def getParameters(self) -> Dict:
        """
        Get the parameters from the dialog.
        """
        pass

    def processingContext(self) -> QgsProcessingContext:
        return QgsProcessingContext()

    def createContext(self) -> QgsProcessingContext:
        return QgsProcessingContext()

    def createFeedback(self) -> QgsProcessingFeedback:
        return super().createFeedback()

    def pushInfo(self, info: str) -> None:
        super().pushInfo(info)

    def pushWarning(self, warning: str) -> None:
        super().pushWarning(warning)

    def reportError(self, error: str, fatalError: bool) -> None:
        super().reportError(error, fatalError)

    def runAlgorithm(self) -> None:
        context = self.processingContext()
        feedback = self.createFeedback()
        local_context.set_feedback(feedback)

        params = self.getParameters()

        self.pushDebugInfo(f"QGIS version: {Qgis.QGIS_VERSION}")
        self.pushDebugInfo(f"QGIS code revision: {Qgis.QGIS_DEV_VERSION}")
        self.pushDebugInfo(f"Qt version: {QT_VERSION_STR}")
        self.pushDebugInfo(f"GDAL version: {gdal.VersionInfo('--version')}")
        try:
            from shapely import geos

            self.pushInfo(f"GEOS version: {geos.geos_version_string}")
        except Exception:
            self.pushInfo("GEOS version: not available")
        self.pushCommandInfo(
            f"Algorithm started at: {datetime.now().isoformat(timespec='seconds')}"
        )
        self.pushCommandInfo(f"Algorithm '{self.algorithm().displayName()}' starting…")
        self.pushCommandInfo("Input parameters:")
        for k, v in params.items():
            self.pushCommandInfo(f"  {k}: {v}")

        results = processing.run(
            self.algorithm(), params, context=context, feedback=feedback
        )
        self.setResults(results)
        self.showLog()

    def algExecuted(self, successful: bool, results: Dict) -> None:
        return super().algExecuted(successful, results)

    def createProcessingParameters(self, flags) -> typing.Dict[str, typing.Any]:
        # TODO: We are currently unable to copy parameters
        #   from the algorithm to the dialog.
        return {}
