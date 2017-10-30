# coding=utf-8
"""DockWidget test.
"""

__author__ = 'gennadiy.donchyts@gmail.com'
__date__ = '2017-06-12'
__copyright__ = 'Copyright 2017, Gennadii Donchyts'

import unittest

from PyQt4.QtGui import QDockWidget

from ee_dock_widget import GoogleEarthEngineDockWidget

from utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class GoogleEarthEngineDockWidgetTest(unittest.TestCase):
    """Test dockwidget works."""

    def setUp(self):
        """Runs before each test."""
        self.dockwidget = GoogleEarthEngineDockWidget(None)

    def tearDown(self):
        """Runs after each test."""
        self.dockwidget = None

    def test_dockwidget_ok(self):
        """Test we can click OK."""
        pass

if __name__ == "__main__":
    suite = unittest.makeSuite(GoogleEarthEngineDockWidgetTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

