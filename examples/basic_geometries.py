import ee
from ee_plugin import Map
ee.Initialize()

point = ee.Geometry.Point([1.5, 1.5])
Map.addLayer(point, {'color': '1eff05'}, 'point')

lineString = ee.Geometry.LineString(
  [[-35, -10], [35, -10], [35, 10], [-35, 10]])
Map.addLayer(lineString, {'color': 'FF0000'}, 'lineString')

linearRing = ee.Geometry.LinearRing(
  [[-35, -10], [35, -10], [35, 10], [-35, 10], [-35, -10]])
Map.addLayer(linearRing, {'color': 'ee38ff'}, 'linearRing')

rectangle = ee.Geometry.Rectangle([-40, -20, 40, 20])
Map.addLayer(rectangle, {'color': 'ffa05c'}, 'rectangle')

polygon = ee.Geometry.Polygon([
  [[-5, 40], [65, 40], [65, 60], [-5, 60], [-5, 60]]
])

planarPolygon = ee.Geometry(polygon, None, False)

Map.addLayer(polygon, {'color': 'FF0000'}, 'geodesic polygon')
Map.addLayer(planarPolygon, {'color': '000000'}, 'planar polygon')

Map.centerObject(polygon)