import ee
from ee_plugin import Map

image = ee.ImageCollection('COPERNICUS/S2') \
  .filterDate('2017-01-01', '2017-01-02').median() \
  .divide(10000) \
  .select(
  ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B12'],
  ['B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B08A', 'B12']
  )
  
vis = {'bands': ['B12', 'B08', 'B04'], 'min': 0.05, 'max': 0.5}
  
Map.addLayer(image, vis, 'S2')

Map.setCenter(35.2, 31, 13)
Map.addLayer(image, {}, 'Sentinel-2 images January, 2018')
