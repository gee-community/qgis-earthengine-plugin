# coding=utf-8
"""Resources test."""

__author__ = "gennadiy.donchyts@gmail.com"
__date__ = "2017-06-12"
__copyright__ = "Copyright 2017, Gennadii Donchyts"

import unittest

from qgis.PyQt.QtGui import QIcon


class GoogleEarthEngineResourcesTest(unittest.TestCase):
    def test_icon_png(self):
        """Test image paths exist"""
        paths = (
            "ee_plugin/icons/google-cloud-project.svg",
            "ee_plugin/icons/google-cloud.svg",
            "ee_plugin/icons/earth-engine.svg",
        )
        for path in paths:
            icon = QIcon(path)
            self.assertFalse(icon.isNull())


if __name__ == "__main__":
    suite = unittest.makeSuite(GoogleEarthEngineResourcesTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
