import typing
from abc import abstractmethod
from datetime import datetime
from typing import Optional, Dict

from osgeo import gdal
from qgis.core import (
    Qgis,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingAlgorithm,
)
from qgis.PyQt.QtCore import Qt, QT_VERSION_STR
from qgis.PyQt.QtWidgets import QWidget
from qgis import gui, processing

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
        self.context = self.createContext()
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
        raise NotImplementedError("buildDialog() not implemented")

    @abstractmethod
    def getParameters(self) -> Dict:
        """
        Get the parameters from the dialog.
        """
        raise NotImplementedError("getParameters() not implemented")

    def processingContext(self) -> QgsProcessingContext:
        return self.context

    def createContext(self) -> QgsProcessingContext:
        return QgsProcessingContext()

    def createFeedback(self) -> QgsProcessingFeedback:
        return super().createFeedback()

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

    def createProcessingParameters(self, flags) -> typing.Dict[str, typing.Any]:
        # TODO: We are currently unable to copy parameters from the algorithm to the dialog.
        #   See: https://github.com/gee-community/qgis-earthengine-plugin/issues/251
        return {}
