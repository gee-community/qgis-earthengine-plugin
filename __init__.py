# -*- coding: utf-8 -*-
import os
<<<<<<< HEAD
=======
import json
import pathlib
import platform
>>>>>>> 5cda083 (Add support for Google Cloud Projects and authenticate/set project at plugin start)
import site
import pkg_resources

PROJECT_NOT_SET_ERROR_MESSAGE = """
Google Earth Engine project is not set.
Starting from November 13, 2024, users need to use a Google Cloud project
to access the Earth Engine platform (https://developers.google.com/earth-engine/guides/transition_to_cloud_projects).
Please configure Google Cloud project by following instructions:
https://developers.google.com/earth-engine/guides/command_line#set_a_cloud_project and then restart QGIS.
"""

<<<<<<< HEAD
def pre_init_plugin():
=======
def add_ee_dependencies():
    if platform.system() == "Windows":
        extlib_path = "extlibs_windows"
    if platform.system() == "Darwin":
        extlib_path = "extlibs_darwin"
    if platform.system() == "Linux":
        extlib_path = "extlibs_linux"
    extra_libs_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), extlib_path)
    )
>>>>>>> 5cda083 (Add support for Google Cloud Projects and authenticate/set project at plugin start)

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

    # load EE python dependencies
    add_ee_dependencies()

    # authenticate and initialize EE
    from . import ee_auth
    ee_auth.authenticate_and_set_project()

    # start
    from .ee_plugin import GoogleEarthEnginePlugin

    return GoogleEarthEnginePlugin(iface)
