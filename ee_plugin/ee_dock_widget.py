# -*- coding: utf-8 -*-
"""
Main dock panel
"""

import os

from qgis.PyQt import uic
from qgis.PyQt.QtCore import pyqtSignal, QUrl

from qgis.gui import QgsDockWidget

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

        # switch tabs
        self.tab_widget.currentChanged.connect(self.tab_activation)

        # home page
        #self.home_plugin_webview.setUrl(QUrl("https://developers.google.com/earth-engine/datasets/catalog/"))

        # catalog tab
        self.catalog_webview.page().mainFrame().initialLayoutCompleted.connect(self.fix_catalog_tab)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def tab_activation(self, tab_index):
        # GEE Catalog
        if tab_index == 1:
            if self.catalog_webview.url().isEmpty():
                self.catalog_webview.setUrl(QUrl("https://developers.google.com/earth-engine/datasets/catalog/"))
        # GEE Doc Api
        if tab_index == 2:
            if self.doc_api_webview.url().isEmpty():
                self.doc_api_webview.load(QUrl("https://developers.google.com/earth-engine/api_docs"))

    def fix_catalog_tab(self):
        # fix thumbnails
        java_script = """
            var styleTag = document.createElement('style');
            styleTag.innerHTML = `
            .ee-datasets-grid .ee-sample-image img {
                display: block !important;
                height: 150px !important;
            }
            .ee-datasets-grid ul.list h3 {
                font-size: 13pt;
                height: unset;
                line-height: 18pt;
                margin-top: 8px;
                margin-bottom: 8px;
                overflow: hidden;
            }
            `
            document.body.appendChild(styleTag);
        """
        self.catalog_webview.page().mainFrame().evaluateJavaScript(java_script)
