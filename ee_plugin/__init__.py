# -*- coding: utf-8 -*-

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Instantiates Google Earth Engine Plugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .ee_plugin import GoogleEarthEnginePlugin
    return GoogleEarthEnginePlugin(iface)
