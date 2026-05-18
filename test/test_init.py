# coding=utf-8
"""Tests QGIS plugin init metadata validation."""

import configparser
import os


def test_metadata_has_required_fields():
    """Test that metadata.txt will validate on plugins.qgis.org."""
    required_metadata = [
        "name",
        "description",
        "qgisMinimumVersion",
        "email",
        "author",
    ]

    file_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            os.pardir,
            "ee_plugin",
            "metadata.txt",
        )
    )

    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(file_path)

    assert parser.has_section("general"), (
        f'Cannot find a section named "general" in {file_path}'
    )

    metadata = dict(parser.items("general"))

    for key in required_metadata:
        assert key in metadata, (
            f'Cannot find metadata "{key}" in metadata source ({file_path}).'
        )
