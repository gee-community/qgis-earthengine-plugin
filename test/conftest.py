from pytest import fixture
from qgis.utils import isPluginLoaded, startPlugin
from qgis.gui import QgisInterface
from PyQt5.QtCore import QSettings, QCoreApplication


@fixture(scope="session", autouse=True)
def load_ee_plugin(qgis_iface: QgisInterface):
    """Load Earth Engine plugin and configure QSettings."""

    # Set QSettings values required by the plugin
    QCoreApplication.setOrganizationName("QGIS")
    QCoreApplication.setApplicationName("QGIS Testing")
    QSettings().setValue("locale/userLocale", "en")

    startPlugin("ee_plugin")
    assert isPluginLoaded("ee_plugin")
    yield qgis_iface
