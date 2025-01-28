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
from typing import Callable, cast, Optional

import requests  # type: ignore
from qgis.core import QgsProject
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import (
    QCoreApplication,
    QSettings,
    QTranslator,
    qVersion,
    QObject,
    Qt,
)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu, QToolButton

PLUGIN_DIR = os.path.dirname(__file__)

# read the plugin version from metadata
cfg = configparser.ConfigParser()
cfg.read(os.path.join(PLUGIN_DIR, "metadata.txt"))
VERSION = cfg.get("general", "version")
version_checked = False


def icon(icon_name: str) -> QIcon:
    """Helper function to return an icon from the plugin directory."""
    return QIcon(os.path.join(PLUGIN_DIR, "icons", icon_name))


class GoogleEarthEnginePlugin(object):
    """QGIS Plugin Implementation."""

    # iface: QgisInterface

    def __init__(self, iface: QgisInterface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        from . import provider

        # Save reference to the QGIS interface
        self.iface = iface

        self.menu = None

        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(
            PLUGIN_DIR, "i18n", "GoogleEarthEnginePlugin_{}.qm".format(locale)
        )
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > "4.3.3":
                QCoreApplication.installTranslator(self.translator)

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
        """Initialize the plugin GUI."""
        # Build actions
        self.ee_user_guide_action = self._build_action(
            text="User Guide",
            icon_name="earth-engine.svg",
            callback=self.run_cmd_ee_user_guide,
        )
        self.sign_in_action = self._build_action(
            text="Sign-in",
            icon_name="google-cloud.svg",
            callback=self.run_cmd_sign_in,
        )
        self.set_cloud_project_action = self._build_action(
            text="Set Project",
            icon_name="google-cloud-project.svg",
            callback=self.run_cmd_set_cloud_project,
        )

        # Build plugin menu
        self.menu = cast(
            QMenu,
            self.iface.pluginMenu().addMenu(
                icon("earth-engine.svg"),
                self.tr("&Google Earth Engine"),
            ),
        )
        self.menu.setDefaultAction(self.ee_user_guide_action)
        self.menu.addAction(self.ee_user_guide_action)
        self.menu.addSeparator()
        self.menu.addAction(self.sign_in_action)
        self.menu.addAction(self.set_cloud_project_action)

        # Build toolbar
        self.toolButton = QToolButton()
        self.toolButton.setMenu(QMenu())
        self.toolButton.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
            if False
            else Qt.ToolButtonStyle.ToolButtonIconOnly
        )
        self.toolButton.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        toolButtonMenu = self.toolButton.menu()

        self.toolButton.setDefaultAction(self.ee_user_guide_action)
        toolButtonMenu.addAction(self.ee_user_guide_action)
        toolButtonMenu.addSeparator()
        toolButtonMenu.addAction(self.sign_in_action)
        toolButtonMenu.addAction(self.set_cloud_project_action)
        self.iface.addToolBarWidget(self.toolButton)

        # Register signal to initialize EE layers on project load
        self.iface.projectRead.connect(self.updateLayers)

    def _build_action(
        self,
        *,
        text: str,
        icon_name: str,
        parent: Optional[QObject] = None,
        callback: Callable,
    ) -> QAction:
        """Helper to add a menu item and connect it to a handler."""
        action = QAction(
            icon(icon_name), self.tr(text), parent or self.iface.mainWindow()
        )
        action.triggered.connect(callback)
        return action

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
        if not self.menu:
            # The initGui() method was never called
            return

        self.iface.pluginMenu().removeAction(self.menu.menuAction())
        self.toolButton.deleteLater()

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
