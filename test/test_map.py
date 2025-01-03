import pytest
import ee
from qgis.core import QgsProject
import Map


@pytest.fixture(scope="module")
def setup_ee():
    """Initialize the Earth Engine API."""
    ee.Initialize()


def test_add_layer(setup_ee, qgis_app):
    """Test adding a layer to the map."""
    # Create an Earth Engine Image
    image = ee.Image("USGS/SRTMGL1_003")
    vis_params = {
        "min": 0,
        "max": 4000,
        "palette": ["006633", "E5FFCC", "662A00", "D8D8D8", "F5F5F5"],
    }
    Map.addLayer(image, vis_params, "DEM")

    # Validate if the layer was added
    layers = QgsProject.instance().mapLayers()
    assert len(layers) > 0, "No layers were added to the map."


def test_set_center(setup_ee, qgis_app):
    """Test setting the map center."""
    lon, lat, zoom = -121.753, 46.855, 9
    Map.setCenter(lon, lat, zoom)

    # Verify the center and zoom
    center = Map.getCenter()
    assert center.getInfo()["coordinates"] == [
        lon,
        lat,
    ], "Center coordinates do not match."
    assert round(Map.getZoom()) == zoom, "Zoom level does not match."


def test_get_bounds(setup_ee, qgis_app):
    """Test getting the bounds of the map."""
    bounds = Map.getBounds()
    assert len(bounds) == 4, "Bounds do not have the expected format."
    assert all(
        isinstance(coord, (float, int)) for coord in bounds
    ), "Bounds coordinates are not numeric."


def test_get_scale(setup_ee, qgis_app):
    """Test getting the map scale."""
    scale = Map.getScale()
    assert scale > 0, "Scale should be a positive number."


def test_set_zoom(setup_ee, qgis_app):
    """Test setting the zoom level."""
    Map.setZoom(10)
    assert round(Map.getZoom()) == 10, "Zoom level was not set correctly."
