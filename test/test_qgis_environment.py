# coding=utf-8
"""Tests for QGIS functionality."""

import os

from qgis.core import QgsCoordinateReferenceSystem, QgsProviderRegistry, QgsRasterLayer


def test_qgis_environment(qgis_app):
    """QGIS environment has the expected providers."""
    r = QgsProviderRegistry.instance()
    providers = r.providerList()

    assert "gdal" in providers
    assert "ogr" in providers
    assert "wms" in providers  # needed for our EE provider


def test_projection(qgis_app):
    """Test that QGIS properly parses a wkt string."""
    crs = QgsCoordinateReferenceSystem()
    wkt = (
        'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",'
        'SPHEROID["WGS_1984",6378137.0,298.257223563]],'
        'PRIMEM["Greenwich",0.0],UNIT["Degree",'
        "0.0174532925199433]]"
    )
    crs.createFromWkt(wkt)
    auth_id = crs.authid()
    expected_auth_id = ["EPSG:4326", "OGC:CRS84"]

    assert auth_id in expected_auth_id

    path = os.path.join(os.path.dirname(__file__), "data", "tenbytenraster.asc")
    layer = QgsRasterLayer(path, "TestRaster")

    assert layer.isValid(), f"Failed to load layer from {path}"

    layer_auth_id = layer.crs().authid()
    assert layer_auth_id in expected_auth_id
