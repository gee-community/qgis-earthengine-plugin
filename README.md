# Google Earth Engine plugin for QGIS

Integrates Google Earth Engine with QGIS using Python API. 

Check [User Guide](https://gee-community.github.io/qgis-earthengine-plugin/) to get started or ask general questions and comments in the [Discussion](https://github.com/gee-community/qgis-earthengine-plugin/discussions) section.

![Add Sentinel-2 image](https://raw.githubusercontent.com/gee-community/qgis-earthengine-plugin/master/media/add_map_layer.png)

### FAQ
Q: I am getting authentication errors, what can I do? 

A: Try installing the Google Earth Engine [command line client](https://developers.google.com/earth-engine/command_line). Run the `earthengine authenticate` command. This resets the authentication credentials and solves most authentication errors.

Q: Are you through a proxy?

A: In your scripts, configure proxy settings on top of them:

```python
import os
os.environ['HTTP_PROXY'] = 'http://[username:password@]<ip_address_or_domain>:<port>'
os.environ['HTTPS_PROXY'] = 'http://[username:password@]<ip_address_or_domain>:<port>'

import ee
from ee_plugin import Map
```

Q: I am getting error like ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed on MacOS:

A: Open Finder and double clicking on this file `/Applications/Python 3.6/Install Certificates.command`. This path may vary depending on how QGIS was installed (Homebrew, macports, native). Then restart QGIS. 

Q: Plugin crashes after authentication with a stack trace showing 404, what should I do?

A: Go to http://code.earthengine.google.com and make sure you can access code editor. If the plugin is still failing - make sure your IP is not under firewall.

### Roadmap

#### Alpha 0.0.1 (Q4 2019) :heavy_check_mark:
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

#### Alpha 0.0.2 (Q3 2020) :heavy_check_mark:
- [x] Upgrade EE library to 0.1.224 (Windows, Linux, maxOS)

#### Alpha 0.0.3 (Q4 2020) :heavy_check_mark:
- [x] EE raster layer inspector
- [x] Show some useful EE properties (bands, value types) in QGIS layer properties dialog
- [x] Fix GEE url authentication function if the credentials is not exists [#63](https://github.com/gee-community/qgis-earthengine-plugin/issues/63)
- [x] Fix crash if the authentication dialog is cancelled or not filled by the user
- [x] Init the Google Earth Engine user authorization system only when the user is going to use the plugin
- [x] Fixed the authentication dialog when the url shortener doesn't work by any reason [#66](https://github.com/gee-community/qgis-earthengine-plugin/issues/66)
- [x] Fix loading extra python dependencies to the plugin, fix [#62](https://github.com/gee-community/qgis-earthengine-plugin/issues/62)

#### Alpha 0.0.4 (Q1 2021) :heavy_check_mark:
- [x] Minor bugfix release (EE authentication)

#### 1.0.0 (Q2 2021) :hourglass:
- [ ] EE vector layer inspector
- [ ] EE raster collection layer inspector
- [ ] Make print(ee_object) more user-friendly, without requiring getInfo(), maybe async
- [ ] Get Link and Open Script
- [ ] Skip import ee and from ee_plugin import Map for EE scripts
...

#### 1.1.0
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

### Support this project

[![Donate](https://www.paypalobjects.com/en_US/NL/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=P2RU23F4ETP4L&item_name=QGIS+Plugin+Development&currency_code=EUR&source=url) or just <a href="https://www.buymeacoffee.com/Eq378D1"><img src="https://cdn.buymeacoffee.com/buttons/default-white.png" width="150"></a>
