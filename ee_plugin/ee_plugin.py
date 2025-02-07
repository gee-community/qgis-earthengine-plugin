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
from qgis import gui
from qgis.PyQt.QtCore import (
    QCoreApplication,
    QSettings,
    QTranslator,
    qVersion,
    QObject,
    Qt,
)

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt import QtWidgets

from .ui.utils import (
    build_form_group_box,
    build_vbox_dialog,
    get_values,
)

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

    def __init__(self, iface: gui.QgisInterface):
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
            callback=self._run_cmd_ee_user_guide,
        )
        self.sign_in_action = self._build_action(
            text="Sign-in",
            icon_name="google-cloud.svg",
            callback=self._run_cmd_sign_in,
        )
        self.set_cloud_project_action = self._build_action(
            text="Set Project",
            icon_name="google-cloud-project.svg",
            callback=self._run_cmd_set_cloud_project,
        )
        self.open_test_widget = self._build_action(
            text="Test dialog",
            icon_name="earth-engine.svg",
            callback=self._test_dock_widget,
        )

        # Build plugin menu
        self.menu = cast(
            QtWidgets.QMenu,
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
        self.toolButton = QtWidgets.QToolButton()
        self.toolButton.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonIconOnly
            # Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.toolButton.setPopupMode(
            QtWidgets.QToolButton.ToolButtonPopupMode.MenuButtonPopup
        )
        self.toolButton.setDefaultAction(self.open_test_widget)
        self.toolButton.setMenu(QtWidgets.QMenu())
        self.toolButton.menu().addAction(self.open_test_widget)
        self.toolButton.menu().addAction(self.ee_user_guide_action)
        self.toolButton.menu().addSeparator()
        self.toolButton.menu().addAction(self.sign_in_action)
        self.toolButton.menu().addAction(self.set_cloud_project_action)
        self.iface.addToolBarWidget(self.toolButton)

        self.iface.addPluginToVectorMenu("My Test", self.ee_user_guide_action)

        # TODO: How to add to Processing Toolbox?

        # Register signal to initialize EE layers on project load
        self.iface.projectRead.connect(self._updateLayers)

    def _build_action(
        self,
        *,
        text: str,
        icon_name: str,
        parent: Optional[QObject] = None,
        callback: Callable,
    ) -> QtWidgets.QAction:
        """Helper to add a menu item and connect it to a handler."""
        action = QtWidgets.QAction(
            icon(icon_name), self.tr(text), parent or self.iface.mainWindow()
        )
        action.triggered.connect(callback)
        return action

    def _run_cmd_ee_user_guide(self):
        # open user guide in external web browser
        webbrowser.open_new("http://qgis-ee-plugin.appspot.com/user-guide")

    def _run_cmd_sign_in(self):
        import ee

        from ee_plugin import ee_auth  # type: ignore

        # reset authentication by forcing sign in
        ee.Authenticate(auth_mode="localhost", force=True)

        # after resetting authentication, select Google Cloud project again
        ee_auth.select_project()

    def _run_cmd_set_cloud_project(self):
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

    def _updateLayers(self):
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

    def _test_dock_widget(self):
        dialog = build_vbox_dialog(
            windowTitle="Add Feature Collection",
            widgets=[
                build_form_group_box(
                    title="Source",
                    rows=[
                        (
                            QtWidgets.QLabel(
                                text="Add GEE Feature Collection to Map",
                                toolTip="This is a tooltip!",
                                whatsThis='This is "WhatsThis"! <a href="http://google.com">Link</a>',
                            ),
                            QtWidgets.QLineEdit(objectName="featureCollectionId"),
                        )
                    ],
                ),
                build_form_group_box(
                    title="Filter by Properties",
                    collapsable=True,
                    collapsed=True,
                    rows=[
                        (
                            "Name",
                            QtWidgets.QLineEdit(objectName="filterName"),
                        ),
                        (
                            "Value",
                            QtWidgets.QLineEdit(objectName="filterValue"),
                        ),
                    ],
                ),
                build_form_group_box(
                    title="Filter by Dates",
                    collapsable=True,
                    collapsed=True,
                    rows=[
                        (
                            "Start",
                            QtWidgets.QDateEdit(objectName="startDate"),
                        ),
                        (
                            "End",
                            QtWidgets.QDateEdit(objectName="endDate"),
                        ),
                    ],
                ),
                gui.QgsExtentGroupBox(
                    objectName="extent",
                    title="Filter by Coordinates",
                    collapsed=True,
                ),
                build_form_group_box(
                    title="Visualization",
                    collapsable=True,
                    collapsed=True,
                    rows=[
                        ("Color", gui.QgsColorButton(objectName="vizColorHex")),
                    ],
                ),
            ],
            accepted=lambda: self.iface.messageBar().pushMessage(
                f"Accepted {get_values(dialog)=}"
            ),
            rejected=lambda: self.iface.messageBar().pushMessage("Cancelled"),
        )
