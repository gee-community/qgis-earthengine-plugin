import json
import ee
from ee_plugin import Map
ee.Initialize()

dem = ee.Image('JAXA/ALOS/AW3D30/V2_2').select('AVE_DSM')
Map.addLayer(dem, { 'min': 0, 'max': 3000 }, 'DEM', True)

# MANUAL STEP: use "Create layer from extent" tool and activate the resulting layer

# get first feature geometry from active layer
layer = iface.activeLayer()
feature = next(layer.getFeatures())
geom = feature.geometry()

geom_json = json.loads(geom.asJson())

# show geometry (double-check)
geom_ee = ee.Geometry.Polygon(geom_json['coordinates'], 'EPSG:3857', False)
Map.addLayer(geom_ee, {}, 'geom')

# download dem using given geometry as region
url = dem.getDownloadURL({
    'name': 'dem',
    'scale': 30,
    'region': json.dumps(geom_ee.getInfo())
})

print(url)
