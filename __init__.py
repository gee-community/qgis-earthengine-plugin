# -*- coding: utf-8 -*-
import os
import platform
import site
import pkg_resources


def pre_init_plugin():
    if platform.system() == "Windows":
        extlib_path = "extlibs_windows"
    if platform.system() == "Darwin":
        extlib_path = "extlibs_darwin"
    if platform.system() == "Linux":
        extlib_path = "extlibs_linux"
    extra_libs_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), extlib_path)
    )

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

    # start
    from .ee_plugin import GoogleEarthEnginePlugin

    return GoogleEarthEnginePlugin(iface)
