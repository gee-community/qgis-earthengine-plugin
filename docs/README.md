This is a home page for QGIS Earth Engine plugin. The ee_plugin adds support for [Google Earth Engine Python API](https://github.com/google/earthengine-api/tree/master/python) to QGIS. 

**Latest version: 0.0.1 pre-alpha (not released yet)**

Once installed, the plugin can be accessed via QGIS Python Console ![](https://docs.qgis.org/3.4/en/_images/iconRunConsole.png) in [`Plugins > Python Console`](https://docs.qgis.org/2.18/en/docs/user_manual/plugins/python_console.html#the-interactive-console). However, it is more convenient to use QGIS Python [`Code Editor`](https://docs.qgis.org/2.18/en/docs/user_manual/plugins/python_console.html#the-code-editor)  ![](https://docs.qgis.org/3.4/en/_images/iconShowEditorConsole.png) to write and execute EE scripts.

Current version of the plugin adds access to the EE Python API to the QGIS environment so that ee package can be used for QGIS scripting.

![Add Sentinel-2 image](https://raw.githubusercontent.com/gee-community/qgis-earthengine-plugin/master/media/add_map_layer.png)

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
- [ ] Upload to QGIS plugin repository: https://plugins.qgis.org/plugins/

#### Alpha 0.2 (Q1 2020)
...

#### Beta
- [ ] Add support for map layers in a way similar to EE Code Editor
- [ ] Add support for Data Catalog, allowing adding assets without the need to write scripts (select time, styling)
- [ ] Custom EE scripts as Processing algorithms, so that users can use it within Graphical Modeller
- [ ] Fetch (cache?) raster assets locally (EE > QGIS), for a given rectangle / CRS, as a Processing tool
- [ ] Export vector and raster data (QGIS > EE) either via Tasks or some other way
- [ ] Use QGIS vector/raster style editors to edit EE layer styles


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

