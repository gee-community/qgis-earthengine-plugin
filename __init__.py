# -*- coding: utf-8 -*-
import os
import platform
import site
import pkg_resources
import builtins


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


def import_ee():
    """This is a wrapper of the Google Earth engine library for the
    purpose of initializing or starting ee authentication when the
    user or the plugin import ee library.
    """
    # we can now import the libraries
    # Work around bug https://github.com/google/earthengine-api/issues/181
    import httplib2

    from ee_plugin.ee_auth import authenticate

    def __wrapping_ee_import__(name, *args, **kwargs):
        _module_ = __builtin_import__(name, *args, **kwargs)
        if name == "ee":
            if not _module_.data._credentials:
                try:
                    _module_.Initialize(http_transport=httplib2.Http())
                except _module_.ee_exception.EEException:
                    if authenticate(ee=_module_):
                        _module_.Initialize(
                            http_transport=httplib2.Http()
                        )  # retry initialization once the user logs in
                    else:
                        print("\nGoogle Earth Engine authorization failed!\n")

        return _module_

    __builtin_import__ = builtins.__import__
    builtins.__import__ = __wrapping_ee_import__


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Instantiates Google Earth Engine Plugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """

    # load extra python dependencies
    pre_init_plugin()

    # wrap the ee library import
    import_ee()

    # start
    from .ee_plugin import GoogleEarthEnginePlugin

    return GoogleEarthEnginePlugin(iface)
