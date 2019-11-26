**Current Version: 0.0.1 pre-alpha (not released yet)**

This is a home page for QGIS Earth Engine plugin. The ee_plugin adds support for [Google Earth Engine Python API](https://github.com/google/earthengine-api/tree/master/python) to QGIS and implements Map API typically used within the [Google Earth Engine Code Editor](https://developers.google.com/earth-engine/getstarted). To get started - please make sure you're familiar with the EE API first and/or check examples.

Once installed in QGIS, the plugin can be accessed from the QGIS Python [`Code Editor`](https://docs.qgis.org/2.18/en/docs/user_manual/plugins/python_console.html#the-code-editor)  ![](https://docs.qgis.org/3.4/en/_images/iconShowEditorConsole.png) to write and execute EE scripts. There is not UI support available yet, you will have to write code!

![Add Sentinel-2 image](https://raw.githubusercontent.com/gee-community/qgis-earthengine-plugin/master/media/add_map_layer.png)

### Map

The plugin implements most of the Map.* functionality typically used in the [Code Editor](https://developers.google.com/earth-engine/playground). Note, that no UI or Layers functionality is supported right now. 

The following Map functions are currently implemented, optional arguments are in _italic_:

* Map.addLayer(eeObject, _visParams, name, shown, opacity_), [example](https://github.com/gee-community/qgis-earthengine-plugin/tree/master/examples/map_add_features.py)
* Map.centerObject(object, _zoom_), [example](https://github.com/gee-community/qgis-earthengine-plugin/tree/master/examples/map_center_object.py)
* Map.getBounds(_asGeoJSON_), [example](https://github.com/gee-community/qgis-earthengine-plugin/tree/master/examples/map_get_bounds.py)
* Map.getCenter(), [example](https://github.com/gee-community/qgis-earthengine-plugin/tree/master/examples/map_get_center.py)
* Map.setCenter(lon, lat, _zoom_), [example](https://github.com/gee-community/qgis-earthengine-plugin/tree/master/examples/map_set_center.py)
* Map.getScale()
* Map.getZoom()
* Map.setZoom(zoom), [example](https://github.com/gee-community/qgis-earthengine-plugin/tree/master/examples/map_set_zoom.py)

Check official [EE API documentation](https://developers.google.com/earth-engine/getstarted#adding-data-to-the-map) for Map usage.

#### Importing plugin

To get started, make sure to include the following two importes at the beginning:

```python
from ee_plugin import Map
import ee
```

After that, the Map.* functions can be used in a similar way to how this is done in Code Editor:

#### Adding map layers

```python
image = ee.Image('USGS/SRTMGL1_003').unitScale(0, 5000)
    
Map.addLayer(image, {'palette': ['blue', 'red'], 'min': 0, 'max': 1000}, 'dem', True)
```

The code above will query Earth Engine for an image and will add it as an XYZ tile layer to the QGIS Canvas. 

Note that QGIS projects containing EE map layers can be also saved, in this case, the code required to connect the to EE is stored in a QGIS project and is used to re-initialize these layers when the project is loaded. Currently, this works only if ee_plugin is installed in the QGIS where these layers are loaded.

Check [examples](https://github.com/gee-community/qgis-earthengine-plugin/tree/master/examples) directory to learn what kind of functionality is currently supported.

