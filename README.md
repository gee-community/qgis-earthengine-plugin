# Google Earth Engine plugin for QGIS

Integrates Google Earth Engine with QGIS using Python API

See [https://gee-community.github.io/qgis-earthengine-plugin/](https://gee-community.github.io/qgis-earthengine-plugin/) for Roadmap and some docs.

![Add Sentinel-2 image](/media/add_map_layer.png)

### Misc

* Wiki: https://github.com/gena/qgis-earthengine-plugin/wiki
* Board: https://github.com/gena/qgis-earthengine-plugin/projects/1

### For Developers

This section is for developers-only. 

The ee_plugin uses paver for packaging. If you do not have paver (https://github.com/paver/paver) installed, install it by typing the following in a console:

```pip install paver```

Open a console in the folder created in the first step, and type

```paver setup```

This will get all the dependencies needed by the plugin.

Install into QGIS by running

```paver install```

This should create a symbolic link to the plugin directory wihin the QGIS plugins deployment directory. Check Settings > User Profiles > Open Active Profile Folder, and then go to python/plugins.

### Random Links

* [Ujaval Gandhi](https://twitter.com/spatialthoughts) - [QGIS Plugin Builder](http://g-sherman.github.io/Qgis-Plugin-Builder/)
* JetBrains - [PyCharm](https://www.jetbrains.com/pycharm/)


