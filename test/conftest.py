import ee
from pytest import fixture
from qgis.utils import plugins
from PyQt5.QtCore import QSettings, QCoreApplication

from ee_plugin import ee_plugin, config


@fixture(scope="session", autouse=True)
def setup_ee():
    """Initialize the Earth Engine API."""
    print("Initializing Earth Engine API...")
    ee.Initialize()
    ee.Authenticate(auth_mode="localhost", quiet=True)


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
