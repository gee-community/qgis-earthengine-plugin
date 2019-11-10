## Google Earth Engine plugin

This plugin allows load into Qgis the google earth engine images (raw or processed) through EE Python API and some (mimic/wrapper) functions of this plugin.

This plugin works using the Qgis's Python console  ![](https://docs.qgis.org/3.4/en/_images/iconRunConsole.png)  in `Plugins > Python Console`. It is recommended use the `Code Editor`  ![](https://docs.qgis.org/3.4/en/_images/iconShowEditorConsole.png) to write and execute scripts.

### Functions emulated

Normally most of the code written in EE Python API runs in Qgis Python console with minimum changes, it's required replacing some functions emulated. The current functions emulated from EE Python API to Qgis Python console are:

- **Map.addLayer**

```python
from ee_plugin import Map

Map.addLayer(image, visParams=None, 
             name=None, shown=True, opacity=1.0)

# Note:
# image: must be a 'ee.Image' instance
```

- **Map.setCenter**

```python
from ee_plugin import Map

Map.setCenter(lon, lat, zoom=None)

# Note:
# lon and lat in geographical values
# zoom (optional) scale level, from 1 to 24
```

### Examples

```python
import ee
ee.Initialize()

from ee_plugin import Map

image = ee.Image('USGS/SRTMGL1_003').unitScale(0, 5000) \
    .visualize(**{'palette': ['blue', 'red']})

Map.addLayer(image, {}, 'dem', True)
```
