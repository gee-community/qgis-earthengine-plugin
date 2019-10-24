from ee_plugin import Map
import ee

image = ee.Image.pixelLonLat() \
    .add([180, 90]).divide([360, 180])

# image = image.multiply(50).sin()

Map.addLayer(image, {}, 'coords', True)


#######

import ee
ee.Initialize()

from ee_plugin import Map
from ee_plugin import utils

image = ee.Image('USGS/SRTMGL1_003').unitScale(0, 5000) \
    .visualize(**{'palette': ['blue', 'red']})

utils.add_or_update_ee_image_layer(image, 'dem')
