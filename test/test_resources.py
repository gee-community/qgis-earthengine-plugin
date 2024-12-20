# coding=utf-8
"""Resources test."""

__author__ = "gennadiy.donchyts@gmail.com"
__date__ = "2017-06-12"
__copyright__ = "Copyright 2017, Gennadii Donchyts"

import unittest

from qgis.PyQt.QtGui import QIcon


class GoogleEarthEngineResourcesTest(unittest.TestCase):
    """Test rerources work."""

    def setUp(self):
        """Runs before each test."""
        pass

    def tearDown(self):
        """Runs after each test."""
        pass

    def test_icon_png(self):
        """Test we can click OK."""
        path = "./icons/earth-engine.svg"
        icon = QIcon(path)
        self.assertFalse(icon.isNull())


if __name__ == "__main__":
    suite = unittest.makeSuite(GoogleEarthEngineResourcesTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
