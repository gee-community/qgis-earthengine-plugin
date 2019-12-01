# -*- coding: utf-8 -*-
import os
import platform
import site

if platform.system() == "Windows":
    extlib_path = '/extlibs_windows'
if platform.system() == "Darwin":
    extlib_path = '/extlibs_darwin'
if platform.system() == "Linux":
    extlib_path = '/extlibs_linux'

site.addsitedir(os.path.abspath(os.path.dirname(__file__) + extlib_path))


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Instantiates Google Earth Engine Plugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """

    #
    from .ee_plugin import GoogleEarthEnginePlugin

    return GoogleEarthEnginePlugin(iface)
