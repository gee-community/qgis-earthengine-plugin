# -*- coding: utf-8 -*-
import configparser
import os
import site


def _plugin_version() -> str:
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(os.path.dirname(__file__), "metadata.txt"))
    try:
        return cfg.get("general", "version")
    except configparser.NoOptionError:
        return "0.0.0-dev"


def add_ee_dependencies():
    extra_libs_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "extlibs")
    )

    if os.path.isdir(extra_libs_path):
        # add to python path
        site.addsitedir(extra_libs_path)


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Instantiates Google Earth Engine Plugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """

    # load EE python dependencies
    add_ee_dependencies()

    # set User Agent for all calls
    import ee

    user_agent = f"QGIS_EE/{_plugin_version()}"
    if ee.data.getUserAgent() != user_agent:
        ee.data.setUserAgent(user_agent)

    # authenticate and initialize EE
    from . import ee_auth, config, ee_plugin

    ee_config = config.EarthEngineConfig()
    ee_auth.ensure_authenticated(ee_config)
    ee_auth.ee_initialize_with_project(ee_config)
    return ee_plugin.GoogleEarthEnginePlugin(iface, ee_config=ee_config)
