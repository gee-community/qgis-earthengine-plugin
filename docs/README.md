## Introduction

This plugin adds support for [Google Earth Engine Python API](https://github.com/google/earthengine-api/tree/master/python) to QGIS.

Once installed, the plugin can be accessed via QGIS Python Console ![](https://docs.qgis.org/3.4/en/_images/iconRunConsole.png) in [`Plugins > Python Console`](https://docs.qgis.org/2.18/en/docs/user_manual/plugins/python_console.html#the-interactive-console). However, it is more convenient to use QGIS Python [`Code Editor`](https://docs.qgis.org/2.18/en/docs/user_manual/plugins/python_console.html#the-code-editor)  ![](https://docs.qgis.org/3.4/en/_images/iconShowEditorConsole.png) to write and execute EE scripts.

### Supported Functionality

Current version of the EE QGIS plugin adds access to the EE Python API within the QGIS environment and implements most of the Map.* functionality typically used in the [Code Editor](https://developers.google.com/earth-engine/playground).

The following functions are currently implemented, optional arguments are in _italic_:

* Map.addLayer(eeObject, _visParams, name, shown, opacity_), [example](../examples/map_add_features.py)
* Map.centerObject(object, _zoom_), [example](../examples/map_center_object.py)
* Map.getBounds(_asGeoJSON_), [example](../examples/map_get_bounds.py)
* Map.getCenter(), [example](../examples/map_get_center.py)
* Map.setCenter(lon, lat, _zoom_), [example](../examples/map_set_center.py)
* Map.getScale()
* Map.getZoom()
* Map.setZoom(zoom), [example](../examples/map_set_zoom.py)

Check official [EE API documentation](https://developers.google.com/earth-engine/getstarted#adding-data-to-the-map) for Map usage.

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

