## Introduction

This plugin adds support for [Google Earth Engine Python API](https://github.com/google/earthengine-api/tree/master/python) to QGIS.

Once installed, the plugin can be accessed via QGIS Python Console ![](https://docs.qgis.org/3.4/en/_images/iconRunConsole.png) in `Plugins > Python Console`. However, it is more convenient to use QGIS Python [`Code Editor`](https://docs.qgis.org/2.18/en/docs/user_manual/plugins/python_console.html#the-code-editor)  ![](https://docs.qgis.org/3.4/en/_images/iconShowEditorConsole.png) to write and execute EE scripts.

### Supported Functionality

Current version of the EE QGIS plugin adds access to the EE Python API within the QGIS environment and implements most of the Map.* functionality typically used in the [Code Editor](https://developers.google.com/earth-engine/playground).

The following functions are currently implemented:

* [Map.addLayer()](https://developers.google.com/earth-engine/api_docs#map.addlayer) - works for images and features or geometries
* [Map.centerObject()](https://developers.google.com/earth-engine/api_docs#map.centetrobject)
* [Map.getBounds()](https://developers.google.com/earth-engine/api_docs#map.getbounds)
* [Map.getCenter()](https://developers.google.com/earth-engine/api_docs#map.getcenter)
* [Map.setCenter()](https://developers.google.com/earth-engine/api_docs#map.setcenter)
* [Map.getScale()](https://developers.google.com/earth-engine/api_docs#map.getscale)
* [Map.getZoom()](https://developers.google.com/earth-engine/api_docs#map.getzoom)
* [Map.setZoom()](https://developers.google.com/earth-engine/api_docs#map.setzoom)

#### Importing plugin

To get started, make sure to include the following two importes at the beginning:

```python
from ee_plugin import Map
import ee
```

After that, the Map.* functions can be used in a similar way to how this is done in Code Editor:

#### Adding map layer to QGIS map

```python
image = ee.Image('USGS/SRTMGL1_003').unitScale(0, 5000)
    
Map.addLayer(image, {'palette': ['blue', 'red'], 'min': 0, 'max': 1000}, 'dem', True)
```

The code above will query Earth Engine for an image and will add it as an XYZ tile layer to the QGIS Canvas. 

Check [examples](../examples) directory for scripts showing how to use these functions.

