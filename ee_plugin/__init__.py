# -*- coding: utf-8 -*-

import os
import sys
import site

if os.name == 'nt':
    extlib_path = '/extlibs_windows'
elif sys.platform == 'darwin':
    extlib_path = '/extlibs_macos'
else:
    extlib_path = '/extlibs_linux'

site.addsitedir(os.path.abspath(os.path.dirname(__file__) + extlib_path))

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QMessageBox

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Instantiates Google Earth Engine Plugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """

    #
    from .ee_plugin import GoogleEarthEnginePlugin

    return GoogleEarthEnginePlugin(iface)
