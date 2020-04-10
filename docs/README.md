**Current Version: 0.0.1 alpha**

[![Gitter](https://badges.gitter.im/gee-community/qgis-earthengine-plugin.svg)](https://gitter.im/gee-community/qgis-earthengine-plugin?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)

The QGIS Earth Engine plugin integrates [Google Earth Engine](http://earthengine.google.com) and [QGIS](https://qgis.org/) using [EE Python API](https://github.com/google/earthengine-api/tree/master/python). Currently, the plugin implements only a subset of Map API typically used within the [Google Earth Engine Code Editor](https://developers.google.com/earth-engine/getstarted). To get started - please make sure you're familiar with the EE first by visiting: https://developers.google.com/earth-engine/getstarted. 

### Installation

The plugin can be installed from the QGIS Plugin Repository as any other plugin. It may take some time install (~30-60 sec) due to EE dependencies included in the distribution. 

The user needs to have an active Google Earth Engine (EE) account to use the plugin. If you don't have one - please sign-up here: https://earthengine.google.com/signup/.

After the installation, the plugin checks if the user is authenticated to use the EE. If this is not the case - the user will be asked to authenticate.

Once installed and authenticated, the plugin can be accessed from the QGIS Python [`Code Editor`](https://docs.qgis.org/2.18/en/docs/user_manual/plugins/python_console.html#the-code-editor)  ![](https://docs.qgis.org/3.4/en/_images/iconShowEditorConsole.png) to write and execute EE scripts. There is not UI support available yet, you will have to write code!

To test if the plugin is installed and authenticated properly - type the following in the QGIS Python Console:

```python
>>> import ee
>>> print(ee.String('Hello World from EE!').getInfo())
Hello World from EE!
```

A more advanced script may look like this:

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

For most of the EE scripts, the following two imports must be included:

```python
import ee
from ee_plugin import Map
```

After that, the Map.* functions can be used in a similar way to the official EE Code Editor [https://developers.google.com/earth-engine/playground]:

#### Adding map layers

```python
image = ee.Image('USGS/SRTMGL1_003')
    
Map.addLayer(image, {'palette': ['blue', 'red'], 'min': 0, 'max': 5000}, 'dem', True)
```

The code above will query Earth Engine for an image and will add it as an XYZ tile layer to the QGIS Canvas. 

Note that QGIS projects containing EE map layers can be also saved, in this case, the code required to connect to EE is stored in a QGIS project and is used to re-initialize these layers when the project is loaded. Currently, this works only if ee_plugin is installed in the QGIS where these layers are loaded.

Check [examples](https://github.com/gee-community/qgis-earthengine-plugin/tree/master/examples) directory to learn what kind of functionality is currently supported.


### Donate

Consider supporting this project:

[![Donate](https://www.paypalobjects.com/en_US/NL/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=P2RU23F4ETP4L&item_name=QGIS+Plugin+Development&currency_code=EUR&source=url) or just <a href="https://www.buymeacoffee.com/Eq378D1"><img src="https://cdn.buymeacoffee.com/buttons/default-white.png" width="150"></a>

