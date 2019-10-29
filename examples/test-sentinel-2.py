from ee_plugin import Map
import ee

image = ee.ImageCollection('COPERNICUS/S2') \
  .filterDate('2018-01-01', '2018-01-02').median() \
  .divide(10000).visualize(**{'bands': ['B12', 'B8', 'B4'], 'min': 0.05, 'max': 0.5})
  
Map.addLayer(image, {}, 'Sentinel-2 images January, 2018')
