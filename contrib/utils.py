import math

import ee


def radians(img):
  """Converts image from degrees to radians"""
  return img.toFloat().multiply(math.pi).divide(180)


def hillshade(az, ze, slope, aspect):
  """Computes hillshade"""
  azimuth = radians(ee.Image.constant(az))
  zenith = radians(ee.Image.constant(90).subtract(ee.Image.constant(ze)))

  return azimuth \
      .subtract(aspect).cos().multiply(slope.sin()).multiply(zenith.sin()) \
      .add(zenith.cos().multiply(slope.cos()))


def hillshadeRGB(image, elevation, weight=1, height_multiplier=5, azimuth=0, zenith=45,
                 contrast=0, brightness=0, saturation=1, castShadows=False, customTerrain=False):
  """Styles RGB image using hillshading, mixes RGB and hillshade using HSV<->RGB transform"""

  hsv = image.visualize().unitScale(0, 255).rgbToHsv()

  z = elevation.multiply(ee.Image.constant(height_multiplier))

  terrain = ee.Algorithms.Terrain(z)
  slope = radians(terrain.select(['slope'])).resample('bicubic')
  aspect = radians(terrain.select(['aspect'])).resample('bicubic')

  if customTerrain:
    raise NotImplementedError('customTerrain argument is not implemented yet')

  hs = hillshade(azimuth, zenith, slope, aspect).resample('bicubic')

  if castShadows:
      hysteresis = True
      neighborhoodSize = 256

      hillShadow = ee.Algorithms.HillShadow(elevation, azimuth,
                                            ee.Number(90).subtract(zenith), neighborhoodSize, hysteresis).float()

      hillShadow = ee.Image(1).float().subtract(hillShadow)

      # opening
      # hillShadow = hillShadow.multiply(hillShadow.focal_min(3).focal_max(6))

      # cleaning
      hillShadow = hillShadow.focal_mode(3)

      # smoothing
      hillShadow = hillShadow.convolve(ee.Kernel.gaussian(5, 3))

      # transparent
      hillShadow = hillShadow.multiply(0.7)

      hs = hs.subtract(hillShadow).rename('shadow')

  intensity = hs.multiply(ee.Image.constant(weight)) \
      .add(hsv.select('value').multiply(ee.Image.constant(1)
                                        .subtract(weight)))

  sat = hsv.select('saturation').multiply(saturation)

  hue = hsv.select('hue')

  result = ee.Image.cat(hue, sat, intensity).hsvToRgb() \
      .multiply(ee.Image.constant(1).float().add(contrast)).add(ee.Image.constant(brightness).float())

  if customTerrain:
      mask = elevation.mask().focal_min(2)

      result = result.updateMask(mask)

  return result
