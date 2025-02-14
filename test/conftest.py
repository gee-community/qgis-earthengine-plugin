import ee
from pytest import fixture
from qgis.utils import plugins, isPluginLoaded
from qgis.gui import QgisInterface
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
def load_ee_plugin(
    qgis_iface: QgisInterface,
    setup_ee: None,
    ee_config: config.EarthEngineConfig,
):
    """Load Earth Engine plugin and configure QSettings."""

    # Set QSettings values required by the plugin
    QCoreApplication.setOrganizationName("QGIS")
    QCoreApplication.setApplicationName("QGIS Testing")
    QSettings().setValue("locale/userLocale", "en")

    # Initialize and register the plugin
    plugin = ee_plugin.GoogleEarthEnginePlugin(iface=qgis_iface, ee_config=ee_config)
    plugin.check_version()

    plugins["ee_plugin"] = plugin
    assert isPluginLoaded("ee_plugin")
    yield qgis_iface
