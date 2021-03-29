# -*- coding: utf-8 -*-
"""
Main plugin file.
"""

from __future__ import absolute_import
import configparser
import requests

import webbrowser
from builtins import object
import os.path
import json

from qgis.PyQt.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProject

from ee_plugin import provider
from ee_plugin.icons import resources

# read the plugin version from metadata
cfg = configparser.ConfigParser()
cfg.read(os.path.join(os.path.dirname(__file__), 'metadata.txt'))
VERSION = cfg.get('general', 'version')
version_checked = False


class GoogleEarthEnginePlugin(object):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GoogleEarthEnginePlugin_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.menu_name_plugin = self.tr("Google Earth Engine Plugin")

        # Create and register the EE data providers
        provider.register_data_provider()

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('GoogleEarthEngine', message)

    def initGui(self):
        ### Main dockwidget menu
        # Create action that will start plugin configuration
        icon_path = ':/plugins/ee_plugin/icons/earth_engine.svg'
        self.dockable_action = QAction(
            QIcon(icon_path), "User Guide", self.iface.mainWindow())
        # connect the action to the run method
        self.dockable_action.triggered.connect(self.run)
        # Add menu item
        self.iface.addPluginToMenu(self.menu_name_plugin, self.dockable_action)
        # Register signal to initialize EE layers on project load
        self.iface.projectRead.connect(self.updateLayers)
         

    def run(self):
        # open user guide in external web browser
        webbrowser.open_new(
            "http://qgis-ee-plugin.appspot.com/user-guide")

    def check_version(self):
        global version_checked
        
        if version_checked:
            return

        try:
            latest_version = requests.get('https://qgis-ee-plugin.appspot.com/get_latest_version').text

            if VERSION < latest_version:
                self.iface.messageBar().pushMessage('Earth Engine plugin:',
                    'There is a more recent version of the ee_plugin available {0} and you have {1}, please upgrade!'.format(latest_version, VERSION), duration=15)
        except: 
            print('Error occurred when checking for recent plugin version, skipping ...')

        finally:
            version_checked = True


    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu(
            self.menu_name_plugin, self.dockable_action)

    def updateLayers(self):
        import ee
        from ee_plugin.utils import add_or_update_ee_layer
        layers = QgsProject.instance().mapLayers().values()

        for l in filter(lambda layer: layer.customProperty('ee-layer'), layers):
            ee_object = l.customProperty('ee-object')
            ee_object_vis = l.customProperty('ee-object-vis')

            # check for backward-compatibility, older file formats (before 0.0.3) store ee-objects in ee-script property an no ee-object-vis is stored
            # also, it seems that JSON representation of persistent object has been changed, making it difficult to read older EE JSON
            if ee_object is None:
                print('\nWARNING:\n Map layer saved with older version of EE plugin is detected, backward-compatibility for versions before 0.0.3 is not supported due to changes in EE library, please re-create EE layer by re-running the Python script\n')
                return

            ee_object = ee.deserializer.fromJSON(ee_object)

            if ee_object_vis is not None:
                ee_object_vis = json.loads(ee_object_vis)
            
            # update loaded EE layer

            # get existing values for name, visibility, and opacity 
            # TODO: this should not be needed, refactor add_or_update_ee_layer to update_ee_layer
            name = l.name()
            shown = QgsProject.instance().layerTreeRoot().findLayer(l.id()).itemVisibilityChecked()
            opacity = l.renderer().opacity()

            add_or_update_ee_layer(ee_object, ee_object_vis, name, shown, opacity)
