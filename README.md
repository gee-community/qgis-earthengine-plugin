# Google Earth Engine plugin for QGIS

Integrates Google Earth Engine with QGIS using Python API. 

Check [User Guide](https://gee-community.github.io/qgis-earthengine-plugin/) to get started.

[![Gitter](https://badges.gitter.im/gee-community/qgis-earthengine-plugin.svg)](https://gitter.im/gee-community/qgis-earthengine-plugin?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)

![Add Sentinel-2 image](https://raw.githubusercontent.com/gee-community/qgis-earthengine-plugin/master/media/add_map_layer.png)

### Support this project

[![Donate](https://www.paypalobjects.com/en_US/NL/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=P2RU23F4ETP4L&item_name=QGIS+Plugin+Development&currency_code=EUR&source=url) or just <a href="https://www.buymeacoffee.com/Eq378D1"><img src="https://cdn.buymeacoffee.com/buttons/default-white.png" width="150"></a>

### FAQ
Q: I am getting authentication errors, what can I do? 

A: Install the Google Earth Engine [command line client](https://developers.google.com/earth-engine/command_line). Run the `earthengine authenticate` command. This resets the authentication credentials and solves most authentication errors.

Q: I am getting error like ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed on MacOS:

A: Open Finder and double clicking on this file `/Applications/Python 3.6/Install Certificates.command`. This path may vary depending on how QGIS was installed (Homebrew, macports, native). Then restart QGIS. 

Q: Plugin crashes after authentication with a stack trace showing 404, what should I do?

A: Go to http://code.earthengine.google.com and make sure you can access code editor. If the plugin is still failing - make sure your IP is not under firewall.

### Roadmap

#### Alpha 0.1 (Q4 2019)
- [x] Create a new QGIS plugin skeleton
- [x] Migrate to QGIS3
- [x] Embed GEE Python library
- [x] Implement Map.addLayer() for ee.Image
- [x] Implement Map.addLayer() for ee.Geometry, ee.Feature and ee.FeatureCollection
- [x] Implement Map.centerObject()
- [x] Implement Map.getBounds()
- [x] Implement Map.getCenter()
- [x] Implement Map.setCenter()
- [x] Implement Map.getScale()
- [x] Implement Map.getZoom()
- [x] Implement Map.setZoom()
- [x] Upload to QGIS plugin repository: https://plugins.qgis.org/plugins/ - approved!

#### Alpha 0.2 (Q1 2020)
- [x] EE raster layer inspector
- [ ] EE vector layer inspector
- [ ] EE raster collection layer inspector
- [ ] Make print(ee_object) more user-friendly, without requiring getInfo(), maybe async
- [ ] Get Link and Open Script
- [ ] Skip import ee and from ee_plugin import Map for EE scripts
...

#### Beta
- [ ] Export.* and Tasks panel (start, cancel, info)
- [ ] Map.layers() for EE layers, allowing to use things like ui.Map.Layer.setEeObject()
- [ ] ui.Chart.*
- [ ] require()
- [ ] Faster identify tool, using local cached rasters
- [ ] Add support for Data Catalog, allowing adding assets without the need to write scripts (select time, styling)
- [ ] Custom EE scripts as Processing algorithms, so that users can use it within Graphical Modeller
- [ ] Fetch (cache?) raster assets locally (EE > QGIS), for a given rectangle / CRS, as a Processing tool
- [ ] Export vector and raster data (QGIS > EE) either via Tasks or some other way
- [ ] Use QGIS vector/raster style editors to edit EE layer styles

### For Developers

This section is for developers-only. 

The ee_plugin uses paver for packaging. If you do not have paver (https://github.com/paver/paver) installed, install it by typing the following in a console:

```
pip install paver
```

Open a console in the folder created in the first step, and type

```
paver setup
```

This will get all the dependencies needed by the plugin.

Install into QGIS by running

```
paver install
```

This should create a symbolic link to the plugin directory wihin the QGIS plugins deployment directory. Check Settings > User Profiles > Open Active Profile Folder, and then go to python/plugins. To reload any changes made in the plugin into Qgis, it is recommended to use the [plugin reloader](https://plugins.qgis.org/plugins/plugin_reloader/).

To generate the installable zip package

```
paver package
``` 

### Random Links

* [Ujaval Gandhi](https://twitter.com/spatialthoughts) - [QGIS Plugin Builder](http://g-sherman.github.io/Qgis-Plugin-Builder/)
* JetBrains - [PyCharm](https://www.jetbrains.com/pycharm/)

