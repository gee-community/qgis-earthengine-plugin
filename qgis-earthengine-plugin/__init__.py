# -*- coding: utf-8 -*-
"""
/***************************************************************************
 EETools
                                 A QGIS plugin
 Earth Engine Tools
                             -------------------
        begin                : 2017-08-11
        copyright            : (C) 2017 by Rodrigo E. Principe
        email                : fitoprincipe82@gmail.com
        git sha              : $Format:%H$
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
