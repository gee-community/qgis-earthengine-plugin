# coding=utf-8
"""Tests that plugin icon resources exist and load."""

import pytest
from qgis.PyQt.QtGui import QIcon


@pytest.mark.parametrize(
    "path",
    [
        "ee_plugin/icons/google-cloud-project.svg",
        "ee_plugin/icons/google-cloud.svg",
        "ee_plugin/icons/earth-engine.svg",
    ],
)
def test_icon_loads(path):
    """Test that icon SVG files load as non-null QIcons."""
    icon = QIcon(path)
    assert not icon.isNull(), f"Icon failed to load: {path}"
