import ee
from ee_plugin import Map

image = ee.Image.pixelLonLat().add([180, 90]).divide([360, 180])

# image = image.multiply(50).sin()

Map.addLayer(image, {}, "coords", True)
Map.setCenter(0, 28, 2.5)
