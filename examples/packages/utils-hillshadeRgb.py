import ee

from ee_plugin import Map
from ee_plugin.packages import utils, palettes

# Note, that this script is quite intense and it may take time to render on EE side

Map.setCenter(4.407, 52.177, 18)

dem = ee.Image("AHN/AHN2_05M_RUW") \
  .resample('bicubic') \
  .convolve(ee.Kernel.gaussian(0.5, 0.25, 'meters'))

# See https://github.com/gee-community/ee-palettes for the full list of supported color palettes
# palette = palettes.crameri['lisbon']['50']
# palette = palettes.crameri['oleron']['50']
# palette = palettes.crameri['roma']['50'][::-1] # reversed
palette = palettes.crameri['batlow']['50']

demRGB = dem.visualize(**{ 'min': -10, 'max': 10, 'palette': palette })
Map.addLayer(demRGB , {}, 'DEM (RGB)', False)

weight = 0.5 # wegith of Hillshade vs RGB intensity (0 - flat, 1 - HS)
exaggeration = 5 # vertical exaggeration
azimuth = 315 # Sun azimuth
zenith = 20 # Sun elevation
brightness = -0.05 # 0 - default
contrast = 0.05 # 0 - default
saturation = 0.8 # 1 - default
castShadows = False

# no shadows
rgb = utils.hillshadeRGB(demRGB, dem, weight, exaggeration, azimuth, zenith, contrast, brightness, saturation, castShadows)
Map.addLayer(rgb, {}, 'DEM (hillshade)', False)

# with shadows
castShadows = True
rgb = utils.hillshadeRGB(demRGB, dem, weight, exaggeration, azimuth, zenith, contrast, brightness, saturation, castShadows)
Map.addLayer(rgb, {}, 'DEM (hillshade, shadows)')

