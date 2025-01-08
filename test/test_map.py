import pytest
from qgis.utils import plugins
from PyQt5.QtCore import QSettings, QCoreApplication

from .. import Map
from ..ee_plugin import GoogleEarthEnginePlugin


@pytest.fixture(scope="module", autouse=True)
def setup_ee():
    """Initialize the Earth Engine API."""
    import ee

    ee.Initialize()
    ee.Authenticate(auth_mode="localhost", quiet=True)


@pytest.fixture(scope="module", autouse=True)
def load_ee_plugin(qgis_app):
    """Load Earth Engine plugin and configure QSettings."""

    # Set QSettings values required by the plugin
    QCoreApplication.setOrganizationName("QGIS")
    QCoreApplication.setApplicationName("QGIS Testing")
    QSettings().setValue("locale/userLocale", "en")

    # Initialize and register the plugin
    plugin = GoogleEarthEnginePlugin(qgis_app)
    plugins["ee_plugin"] = plugin
    plugin.check_version()


def test_add_layer():
    """Test adding a layer to the map."""
    import ee

    image = ee.Image("USGS/SRTMGL1_003")
    vis_params = {
        "min": 0,
        "max": 4000,
        "palette": ["006633", "E5FFCC", "662A00", "D8D8D8", "F5F5F5"],
    }

    # Add the layer to the map
    Map.addLayer(image, vis_params, "DEM")


def test_get_bounds():
    """Test getting the bounds of the map."""
    bounds = Map.getBounds()
    assert len(bounds) == 4, "Bounds do not have the expected format."
    assert all(
        isinstance(coord, (float, int)) for coord in bounds
    ), "Bounds coordinates are not numeric."


def test_get_scale():
    """Test getting the map scale."""
    scale = Map.getScale()
    assert scale > 0, "Scale should be a positive number."
