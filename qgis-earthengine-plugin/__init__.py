# -*- coding: utf-8 -*-
"""
/***************************************************************************
 EarthEnginePlugin
                                 A QGIS plugin
 Integrates QGIS with Google Earth Engine
                              -------------------
        begin                : 2017-06-12
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Gennadii Donchyts
        email                : gennadiy.donchyts@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load EETools class from file EETools.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .earth_engine import EarthEnginePlugin
    return EarthEnginePlugin(iface)
