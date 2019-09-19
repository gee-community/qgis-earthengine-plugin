#!/usr/bin/env python
"""
Main dock panel
"""

import os

from qgis.PyQt import QtGui, uic
from qgis.PyQt.QtCore import pyqtSignal

from qgis.gui import QgsDockWidget

from ee_plugin.ee_catalog import Dataset

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ee_dock_widget_base.ui'))


class GoogleEarthEngineDockWidget(QgsDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(GoogleEarthEngineDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
