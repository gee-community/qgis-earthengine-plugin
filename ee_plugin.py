# -*- coding: utf-8 -*-
"""
Main plugin file.
"""

from __future__ import absolute_import

import configparser
import json
import os.path
import webbrowser
from builtins import object

import requests  # type: ignore
from qgis.core import QgsProject
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator, qVersion
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from ee_plugin import provider

# read the plugin version from metadata
cfg = configparser.ConfigParser()
cfg.read(os.path.join(os.path.dirname(__file__), "metadata.txt"))
VERSION = cfg.get("general", "version")
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
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(
            self.plugin_dir, "i18n", "GoogleEarthEnginePlugin_{}.qm".format(locale)
        )

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > "4.3.3":
                QCoreApplication.installTranslator(self.translator)

        self.menu_name_plugin = self.tr("Google Earth Engine")

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
        return QCoreApplication.translate("GoogleEarthEngine", message)

    def initGui(self):
        ### Main dockwidget menu
        # Create action that will start plugin configuration
        ee_icon_path = ":/plugins/ee_plugin/icons/earth-engine.svg"
        self.cmd_ee_user_guide = QAction(
            QIcon(ee_icon_path), "User Guide", self.iface.mainWindow()
        )
        self.cmd_ee_user_guide.triggered.connect(self.run_cmd_ee_user_guide)

        gcp_icon_path = ":/plugins/ee_plugin/icons/google-cloud.svg"
        self.cmd_sign_in = QAction(
            QIcon(gcp_icon_path), "Sign-in", self.iface.mainWindow()
        )
        self.cmd_sign_in.triggered.connect(self.run_cmd_sign_in)

        gcp_project_icon_path = ":/plugins/ee_plugin/icons/google-cloud-project.svg"
        self.cmd_set_cloud_project = QAction(
            QIcon(gcp_project_icon_path), "Set Project", self.iface.mainWindow()
        )
        self.cmd_set_cloud_project.triggered.connect(self.run_cmd_set_cloud_project)

        # Add menu item
        self.iface.addPluginToMenu(self.menu_name_plugin, self.cmd_ee_user_guide)
        self.iface.addPluginToMenu(self.menu_name_plugin, self.cmd_sign_in)
        self.iface.addPluginToMenu(self.menu_name_plugin, self.cmd_set_cloud_project)

        # Register signal to initialize EE layers on project load
        self.iface.projectRead.connect(self.updateLayers)

    def run_cmd_ee_user_guide(self):
        # open user guide in external web browser
        webbrowser.open_new("http://qgis-ee-plugin.appspot.com/user-guide")

    def run_cmd_sign_in(self):
        import ee

        from ee_plugin import ee_auth  # type: ignore

        # reset authentication by forcing sign in
        ee.Authenticate(auth_mode="localhost", force=True)

        # after resetting authentication, select Google Cloud project again
        ee_auth.select_project()

    def run_cmd_set_cloud_project(self):
        from ee_plugin import ee_auth  # type: ignore

        ee_auth.select_project()

    def check_version(self):
        global version_checked

        if version_checked:
            return

        try:
            # Attempt to get the latest version from the server
            latest_version = requests.get(
                "https://qgis-ee-plugin.appspot.com/get_latest_version",
                # requires requests > 2.4, can through requests.exceptions.Timeout (which is a RequestException, so already handled)
                timeout=10,
            ).text

            if VERSION < latest_version:
                self.iface.messageBar().pushMessage(
                    "Earth Engine plugin:",
                    "There is a more recent version of the ee_plugin available {0} and you have {1}, please upgrade!".format(
                        latest_version, VERSION
                    ),
                    duration=15,
                )
        except requests.RequestException as e:
            print(f"HTTP error occurred when checking for recent plugin version: {e}")
        except ValueError as e:
            print(f"Value error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            version_checked = True

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu(self.menu_name_plugin, self.cmd_ee_user_guide)
        self.iface.removePluginMenu(self.menu_name_plugin, self.cmd_sign_in)
        self.iface.removePluginMenu(self.menu_name_plugin, self.cmd_set_cloud_project)

    def updateLayers(self):
        import ee

        from .utils import add_or_update_ee_layer

        layers = QgsProject.instance().mapLayers().values()

        for layer in filter(lambda layer: layer.customProperty("ee-layer"), layers):
            ee_object = layer.customProperty("ee-object")
            ee_object_vis = layer.customProperty("ee-object-vis")

            # check for backward-compatibility, older file formats (before 0.0.3) store ee-objects in ee-script property an no ee-object-vis is stored
            # also, it seems that JSON representation of persistent object has been changed, making it difficult to read older EE JSON
            if ee_object is None:
                print(
                    "\nWARNING:\n Map layer saved with older version of EE plugin is detected, backward-compatibility for versions before 0.0.3 is not supported due to changes in EE library, please re-create EE layer by re-running the Python script\n"
                )
                return

            ee_object = ee.deserializer.fromJSON(ee_object)

            if ee_object_vis is not None:
                ee_object_vis = json.loads(ee_object_vis)

            # update loaded EE layer

            # get existing values for name, visibility, and opacity
            # TODO: this should not be needed, refactor add_or_update_ee_layer to update_ee_layer
            name = layer.name()
            shown = (
                QgsProject.instance()
                .layerTreeRoot()
                .findLayer(layer.id())
                .itemVisibilityChecked()
            )
            opacity = layer.renderer().opacity()

            add_or_update_ee_layer(ee_object, ee_object_vis, name, shown, opacity)
