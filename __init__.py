# -*- coding: utf-8 -*-
import os
import site
import pkg_resources


def pre_init_plugin():

    extra_libs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'extlibs'))

    if os.path.isdir(extra_libs_path):
        # add to python path
        site.addsitedir(extra_libs_path)
        # pkg_resources doesn't listen to changes on sys.path.
        pkg_resources.working_set.add_entry(extra_libs_path)


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Instantiates Google Earth Engine Plugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """

    # load extra python dependencies
    pre_init_plugin()

    # Initialize the Earth Engine Python API
    import ee
    ee.Initialize()

    # start
    from .ee_plugin import GoogleEarthEnginePlugin

    return GoogleEarthEnginePlugin(iface)
