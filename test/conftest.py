import ee
from pytest import fixture
from qgis.core import QgsProject
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import QSettings, QCoreApplication
from qgis.utils import plugins

from ee_plugin import ee_plugin, config


@fixture(scope="session", autouse=True)
def setup_ee():
    """Authenticate and initialize the Earth Engine API."""
    print("Initializing Earth Engine API...")
    ee.Authenticate(auth_mode="localhost", quiet=True)
    ee.Initialize()


@fixture(scope="session", autouse=True)
def ee_config():
    return config.EarthEngineConfig()


@fixture(scope="session", autouse=True)
def load_ee_plugin(qgis_app, setup_ee, ee_config):
    """Load Earth Engine plugin and configure QSettings."""

    # Set QSettings values required by the plugin
    QCoreApplication.setOrganizationName("QGIS")
    QCoreApplication.setApplicationName("QGIS Testing")
    QSettings().setValue("locale/userLocale", "en")

    # Initialize and register the plugin
    plugin = ee_plugin.GoogleEarthEnginePlugin(qgis_app, ee_config=ee_config)
    plugins["ee_plugin"] = plugin
    plugin.check_version()
    yield qgis_app


@fixture(autouse=True, scope="function")
def clean_qgis_iface(qgis_iface: QgisInterface):
    QgsProject.instance().removeAllMapLayers()
    qgis_iface.mapCanvas().setLayers([])
    yield qgis_iface
    QgsProject.instance().removeAllMapLayers()
    qgis_iface.mapCanvas().setLayers([])
