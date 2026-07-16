# -*- coding: utf-8 -*-
"""
Main plugin file.
"""

import configparser
import json
import os.path
import webbrowser
from typing import cast

import requests  # type: ignore
from qgis import gui, processing
from qgis.core import QgsProject, QgsApplication
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator, Qt
from qgis.PyQt.QtGui import QIcon
import ee

from . import provider, config, ee_auth, utils, logging
from .identify import EarthEngineIdentifyTool
from .ui import menus
from .processing.processing_provider import EEProcessingProvider
from .processing.add_image_collection import (
    AddImageCollectionAlgorithm,
    AddImageCollectionAlgorithmDialog,
)

PLUGIN_DIR = os.path.dirname(__file__)

# read the plugin version from metadata
cfg = configparser.ConfigParser()
cfg.read(os.path.join(PLUGIN_DIR, "metadata.txt"))

try:
    VERSION = cfg.get("general", "version")
except configparser.NoOptionError:
    # if version is not set, use a default value
    VERSION = "0.0.0-dev"

version_checked = False


def _parse_version(version: str) -> tuple[int, ...]:
    normalized = version.strip().lstrip("v")
    return tuple(int(part) for part in normalized.split("."))


def icon(icon_name: str) -> QIcon:
    """Helper function to return an icon from the plugin directory."""
    return QIcon(os.path.join(PLUGIN_DIR, "icons", icon_name))


class GoogleEarthEnginePlugin(object):
    """QGIS Plugin Implementation."""

    ee_config: config.EarthEngineConfig

    def __init__(self, iface: gui.QgisInterface, ee_config: config.EarthEngineConfig):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """

        # Save reference to the QGIS interface
        self.iface = iface

        self.ee_config = ee_config
        self.menu = None
        self.toolButton = None
        self.toolButtonAction = None
        self.identify_action = None
        self.identify_tool = None

        # initialize locale
        locale = str(QSettings().value("locale/userLocale"))[0:2]
        locale_path = os.path.join(
            PLUGIN_DIR, "i18n", "GoogleEarthEnginePlugin_{}.qm".format(locale)
        )
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Create and register the EE data providers
        provider.register_data_provider()

        # Reload the plugin when the config changes
        self.ee_config.signals.updated.connect(
            lambda: self.set_cloud_project_action.setText(
                self.tr(self._project_button_text)
            )
        )

        logging.setup_logger(plugin_name="Google Earth Engine Plugin")

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        return utils.translate(message)

    def initGui(self):
        """Initialize the plugin GUI."""

        self.provider = EEProcessingProvider(icon=icon("earth-engine.svg"))
        QgsApplication.processingRegistry().addProvider(self.provider)

        # Build actions
        ee_user_guide_action = QtWidgets.QAction(
            icon=icon("earth-engine.svg"),
            text=self.tr("User Guide"),
            parent=self.iface.mainWindow(),
            triggered=self._run_cmd_ee_user_guide,
        )
        sign_in_action = QtWidgets.QAction(
            icon=icon("google-cloud.svg"),
            text=self.tr("Sign-in"),
            parent=self.iface.mainWindow(),
            triggered=self._run_cmd_sign_in,
        )
        self.set_cloud_project_action = QtWidgets.QAction(
            icon=icon("google-cloud-project.svg"),
            text=self.tr(self._project_button_text),
            parent=self.iface.mainWindow(),
            triggered=self._run_cmd_set_cloud_project,
        )
        add_fc_button = QtWidgets.QAction(
            text=self.tr("Add Feature Collection"),
            parent=self.iface.mainWindow(),
            triggered=lambda: processing.execAlgorithmDialog(
                "ee:add_feature_collection"
            ),
        )

        add_ee_image_button = QtWidgets.QAction(
            text=self.tr("Add Image"),
            parent=self.iface.mainWindow(),
            triggered=lambda: processing.execAlgorithmDialog("ee:add_ee_image"),
        )

        add_image_collection_button = QtWidgets.QAction(
            text=self.tr("Add Image Collection"),
            parent=self.iface.mainWindow(),
            triggered=lambda: AddImageCollectionAlgorithmDialog(
                AddImageCollectionAlgorithm(), self.iface.mainWindow()
            ).exec(),
        )

        export_geotiff_button = QtWidgets.QAction(
            text=self.tr("Export as GeoTIFF"),
            parent=self.iface.mainWindow(),
            triggered=lambda: processing.execAlgorithmDialog("ee:export_geotiff"),
        )

        self.identify_action = QtWidgets.QAction(
            icon=QgsApplication.getThemeIcon("/mActionIdentify.svg"),
            text=self.tr("Identify Earth Engine Pixel or Region"),
            parent=self.iface.mainWindow(),
        )
        self.identify_action.setCheckable(True)
        self.identify_action.triggered.connect(self._toggle_identify_tool)
        self.identify_tool = EarthEngineIdentifyTool(self.iface)
        self.identify_tool.setAction(self.identify_action)

        # Initialize plugin menu
        plugin_menu = cast(QtWidgets.QMenu, self.iface.pluginMenu())
        self.menu = plugin_menu.addMenu(
            icon("earth-engine.svg"),
            self.tr("&Google Earth Engine"),
        )

        # Initialize toolbar menu
        self.toolButton = QtWidgets.QToolButton()
        self.toolButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.toolButton.setPopupMode(
            QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup
        )
        self.toolButton.setMenu(QtWidgets.QMenu())
        self.toolButton.setDefaultAction(
            QtWidgets.QAction(
                icon=icon("earth-engine.svg"),
                text=f"<strong>{self.tr('Google Earth Engine')}</strong>",
                parent=self.iface.mainWindow(),
            )
        )
        self.toolButtonAction = self.iface.pluginToolBar().addWidget(self.toolButton)

        # Populate menus
        for m in (self.menu, self.toolButton.menu()):
            menus.populate_menu(
                menu=m,
                items=[
                    menus.Action(action=ee_user_guide_action),
                    menus.Separator(),
                    menus.Action(action=sign_in_action),
                    menus.Action(action=self.set_cloud_project_action),
                    menus.Separator(),
                    menus.SubMenu(
                        label=self.tr("Add Layer"),
                        subitems=[
                            menus.Action(action=add_fc_button),
                            menus.Action(action=add_ee_image_button),
                            menus.Action(action=add_image_collection_button),
                        ],
                    ),
                    menus.Action(action=self.identify_action),
                    menus.SubMenu(
                        label=self.tr("Export"),
                        subitems=[menus.Action(action=export_geotiff_button)],
                    ),
                ],
            )

        # Register signal to initialize EE layers on project load
        self.iface.projectRead.connect(self._updateLayers)

    def unload(self):
        if (
            self.identify_tool
            and self.iface.mapCanvas().mapTool() is self.identify_tool
        ):
            self.iface.mapCanvas().unsetMapTool(self.identify_tool)

        if self.menu:
            self.iface.pluginMenu().removeAction(self.menu.menuAction())

        if getattr(self, "toolButtonAction", None):
            self.iface.pluginToolBar().removeAction(self.toolButtonAction)

        try:
            if self.toolButton:
                self.toolButton.deleteLater()
        except RuntimeError as e:
            print(f"Error deleting toolButton: {e}")

        if self.provider in QgsApplication.processingRegistry().providers():
            QgsApplication.processingRegistry().removeProvider(self.provider)

        logging.teardown_logger()

    def _toggle_identify_tool(self, checked):
        canvas = self.iface.mapCanvas()
        if checked:
            canvas.setMapTool(self.identify_tool)
        elif canvas.mapTool() is self.identify_tool:
            canvas.unsetMapTool(self.identify_tool)

    @property
    def _project_button_text(self):
        """Get the text for the project button."""
        return f"Set Project: {self.ee_config.project or '...'}"

    def _run_cmd_ee_user_guide(self):
        # open user guide in external web browser
        webbrowser.open_new("http://qgis-ee-plugin.appspot.com/user-guide")

    def _run_cmd_sign_in(self):
        # reset authentication by forcing sign in
        if not ee_auth.ee_authenticate(self.ee_config):
            return

        # after resetting authentication, select Google Cloud project again
        self._run_cmd_set_cloud_project()

    def _run_cmd_set_cloud_project(self):
        ee_auth.ee_initialize_with_project(self.ee_config, force=True)

    def check_version(self):
        global version_checked

        if version_checked:
            return

        try:
            # Compare against the latest published release tag, not main, so
            # users are only prompted about versions that have actually shipped.
            response = requests.get(
                "https://api.github.com/repos/gee-community/qgis-earthengine-plugin/releases/latest",
                # requires requests > 2.4, can through requests.exceptions.Timeout (which is a RequestException, so already handled)
                timeout=10,
            )
            response.raise_for_status()

            latest_version = response.json().get("tag_name", "").lstrip("v")
            if latest_version and _parse_version(VERSION) < _parse_version(
                latest_version
            ):
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

    def _updateLayers(self):
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

            utils.add_or_update_ee_layer(ee_object, ee_object_vis, name, shown, opacity)
