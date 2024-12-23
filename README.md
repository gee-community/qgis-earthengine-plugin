### Support Ukraine

[![Stand With Ukraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner2-direct.svg)](https://vshymanskyy.github.io/StandWithUkraine/)

# Google Earth Engine plugin for QGIS

Integrates Google Earth Engine with QGIS using Python API. 

Check [User Guide](https://gee-community.github.io/qgis-earthengine-plugin/) to get started or ask general questions and comments in the [Discussion](https://github.com/gee-community/qgis-earthengine-plugin/discussions) section.

![Add Sentinel-2 image](https://raw.githubusercontent.com/gee-community/qgis-earthengine-plugin/master/media/add_map_layer.png)

### How to use with a simple example

```python
import ee
from ee_plugin import Map

# Add Earth Engine dataset
image = ee.Image('USGS/SRTMGL1_003')
vis_params = {'min': 0, 'max': 4000, 'palette': ['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']}
Map.addLayer(image, vis_params, 'DEM')
Map.setCenter(-121.753, 46.855, 9)
```

### Troubleshooting

#### How to reset your authentication settings?

Install the Google Earth Engine [command line client](https://developers.google.com/earth-engine/command_line). Run the `earthengine authenticate` command. This resets the authentication credentials and solves most authentication errors.

An alternative is to delete the credentials file and re-authenticate the plugin by restarting the QGIS. 

The credentials file is located in:

```
Windows: C:\Users\<USER>\.config\earthengine\credentials 
Linux: /home/<USER>/.config/earthengine/credentials 
MacOS: /Users/<USER>/.config/earthengine/credentials
```

More about EE authentication guide and troubleshooting [here](https://developers.google.com/earth-engine/guides/auth).

#### Are you through a proxy?

In your scripts, configure proxy settings on top of them:

```python
import os
os.environ['HTTP_PROXY'] = 'http://[username:password@]<ip_address_or_domain>:<port>'
os.environ['HTTPS_PROXY'] = 'http://[username:password@]<ip_address_or_domain>:<port>'

import ee
from ee_plugin import Map
```

#### I am getting error like ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed on MacOS:

Open Finder and double clicking on this file `/Applications/Python 3.6/Install Certificates.command`. This path may vary depending on how QGIS was installed (Homebrew, macports, native). Then restart QGIS. 

#### Plugin crashes after authentication with a stack trace showing 404, what should I do?

Go to http://code.earthengine.google.com and make sure you can access code editor. If the plugin is still failing - make sure your IP is not under firewall.

### Roadmap

#### Alpha 0.0.1 (Q4 2019) :heavy_check_mark:
- [x] Create a new QGIS plugin skeleton
- [x] Migrate to QGIS3
- [x] Embed EE Python library
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
- [x] Fix EE url authentication function if the credentials is not exists [#63](https://github.com/gee-community/qgis-earthengine-plugin/issues/63)
- [x] Fix crash if the authentication dialog is cancelled or not filled by the user
- [x] Init the Google Earth Engine user authorization system only when the user is going to use the plugin
- [x] Fixed the authentication dialog when the url shortener doesn't work by any reason [#66](https://github.com/gee-community/qgis-earthengine-plugin/issues/66)
- [x] Fix loading extra python dependencies to the plugin, fix [#62](https://github.com/gee-community/qgis-earthengine-plugin/issues/62)

#### Alpha 0.0.4 (Q1 2021) :heavy_check_mark:
- [x] Minor bugfix release (EE authentication)

#### Alpha 0.0.5 (Q1 2022) :heavy_check_mark:
- [x] Minor bugfix release (EE library upgrade)

#### Alpha 0.0.6 (Q1 2023) :heavy_check_mark:
- [x] Added support for QGIS 3.22+ (fix identify tool)

### Beta 0.0.7 (Q4 2024) :heavy_check_mark:
- [x] Added support for Google Cloud Projects 
- [x] Added UI to change Google Cloud Project and re-login

#### 1.0.0 (Q4 2025) :hourglass:
- [ ] Improve authentication (UI and error handling)
- [ ] Simplify interpoerability of features/geometry between EE and QGIS
- [ ] Add layer as a child layer to the group layer [#101](https://github.com/gee-community/qgis-earthengine-plugin/issues/101)
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

### Contributing

We warmly welcome contributions of any kind and deeply appreciate all our contributors, large and small, who are listed on the [GitHub Contributors page](https://github.com/gee-community/qgis-earthengine-plugin/graphs/contributors).

If you'd like to contribute, please:
1. Check out the [CONTRIBUTING.md](CONTRIBUTING.md) file for detailed instructions on setting up your local environment.
2. Ensure your contribution relates to an existing issue or discussion topic in the repository. If you're unsure, feel free to open an issue to discuss your idea before starting.

For any questions or concerns, please don't hesitate to contact the original author: [gennadiy.donchyts@gmail.com](mailto:gennadiy.donchyts@gmail.com).

Thank you for helping improve the QGIS Earth Engine Plugin!
