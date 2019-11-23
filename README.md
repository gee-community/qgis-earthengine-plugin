# Google Earth Engine plugin for QGIS

Integrates Google Earth Engine with QGIS using Python API

### Status

* Pre-alpha

### Roadmap

#### Alpha 0.1 (Q4 2019)
- [x] Create a new QGIS plugin skeleton
- [x] Migrate to QGIS3
- [x] Embed GEE Python library
       * test install using https://landscapearchaeology.org/2018/installing-python-packages-in-qgis-3-for-windows/
- [x] Enable raster layer visualization as a tile layer
- [ ] Upload to QGIS plugin repository: https://plugins.qgis.org/plugins/

#### Alpha 0.2 (Q1 2020)
...

#### Beta
- [ ] Add support for Data Catalog, allowing adding assets without the need to write scripts (select time, styling)
- [ ] Custom EE scripts as Processing algorithms, so that users can use it within Graphical Modeller
- [ ] Fetch (cache?) raster assets locally (EE > QGIS), for a given rectangle / CRS, as a Processing tool
- [ ] Export vector and raster data (QGIS > EE) either via Tasks or some other way
- [ ] Use QGIS vector/raster style editors to edit EE layer styles

### Misc

* Wiki: https://github.com/gena/qgis-earthengine-plugin/wiki
* Board: https://github.com/gena/qgis-earthengine-plugin/projects/1

### Contributors

Gennadii Donchyts (@gena)
Xavier Corredor Llano (@XavierCLL)
Hessel Winsemius (@hcwinsemius)

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


