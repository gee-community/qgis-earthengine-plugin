# coding=utf-8
"""Safe Translations Test."""

import os

import pytest
from qgis.PyQt.QtCore import QCoreApplication, QTranslator


@pytest.fixture(autouse=True)
def clean_lang_env(monkeypatch):
    """Ensure LANG is not set during translation tests."""
    monkeypatch.delenv("LANG", raising=False)


def test_qgis_translations(qgis_app):
    """Test that translations work."""
    parent_path = os.path.join(os.path.dirname(__file__), os.path.pardir)
    dir_path = os.path.abspath(parent_path)
    file_path = os.path.join(dir_path, "ee_plugin", "i18n", "af.qm")

    assert os.path.exists(file_path), f"Translation file not found: {file_path}"

    translator = QTranslator()
    loaded = translator.load(file_path)
    assert loaded, f"Failed to load translation file: {file_path}"

    QCoreApplication.installTranslator(translator)

    expected_message = "Goeie more"
    real_message = QCoreApplication.translate("@default", "Good morning")

    assert real_message == expected_message
