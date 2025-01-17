import ee
from pytest import fixture
from qgis.utils import plugins
from PyQt5.QtCore import QSettings, QCoreApplication

from ee_plugin.ee_plugin import GoogleEarthEnginePlugin


@fixture(scope="session", autouse=True)
def setup_ee():
    """Initialize the Earth Engine API."""
    print("Initializing Earth Engine API...")
    ee.Initialize()
    ee.Authenticate(auth_mode="localhost", quiet=True)


@fixture(scope="session", autouse=True)
def load_ee_plugin(qgis_app, setup_ee):
    """Load Earth Engine plugin and configure QSettings."""

    # Set QSettings values required by the plugin
    QCoreApplication.setOrganizationName("QGIS")
    QCoreApplication.setApplicationName("QGIS Testing")
    QSettings().setValue("locale/userLocale", "en")

    # Initialize and register the plugin
    plugin = GoogleEarthEnginePlugin(qgis_app)
    plugins["ee_plugin"] = plugin
    plugin.check_version()
    yield qgis_app
