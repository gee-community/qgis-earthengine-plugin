import math

import ee


def radians(img):
    """Converts image from degrees to radians"""
    return img.toFloat().multiply(math.pi).divide(180)


def hillshade(az, ze, slope, aspect):
    """Computes hillshade"""
    azimuth = radians(ee.Image.constant(az))
    zenith = radians(ee.Image.constant(90).subtract(ee.Image.constant(ze)))

    return (
        azimuth.subtract(aspect)
        .cos()
        .multiply(slope.sin())
        .multiply(zenith.sin())
        .add(zenith.cos().multiply(slope.cos()))
    )


def hillshadeRGB(
    image,
    elevation,
    weight=1,
    height_multiplier=5,
    azimuth=0,
    zenith=45,
    contrast=0,
    brightness=0,
    saturation=1,
    castShadows=False,
    customTerrain=False,
):
    """Styles RGB image using hillshading, mixes RGB and hillshade using HSV<->RGB transform"""

    hsv = image.visualize().unitScale(0, 255).rgbToHsv()

    z = elevation.multiply(ee.Image.constant(height_multiplier))

    terrain = ee.Algorithms.Terrain(z)
    slope = radians(terrain.select(["slope"])).resample("bicubic")
    aspect = radians(terrain.select(["aspect"])).resample("bicubic")

    if customTerrain:
        raise NotImplementedError("customTerrain argument is not implemented yet")

    hs = hillshade(azimuth, zenith, slope, aspect).resample("bicubic")

    if castShadows:
        hysteresis = True
        neighborhoodSize = 256

        hillShadow = ee.Algorithms.HillShadow(
            elevation,
            azimuth,
            ee.Number(90).subtract(zenith),
            neighborhoodSize,
            hysteresis,
        ).float()

        hillShadow = ee.Image(1).float().subtract(hillShadow)

        # opening
        # hillShadow = hillShadow.multiply(hillShadow.focal_min(3).focal_max(6))

        # cleaning
        hillShadow = hillShadow.focal_mode(3)

        # smoothing
        hillShadow = hillShadow.convolve(ee.Kernel.gaussian(5, 3))

        # transparent
        hillShadow = hillShadow.multiply(0.7)

        hs = hs.subtract(hillShadow).rename("shadow")

    intensity = hs.multiply(ee.Image.constant(weight)).add(
        hsv.select("value").multiply(ee.Image.constant(1).subtract(weight))
    )

    sat = hsv.select("saturation").multiply(saturation)

    hue = hsv.select("hue")

    result = (
        ee.Image.cat(hue, sat, intensity)
        .hsvToRgb()
        .multiply(ee.Image.constant(1).float().add(contrast))
        .add(ee.Image.constant(brightness).float())
    )

    if customTerrain:
        mask = elevation.mask().focal_min(2)

        result = result.updateMask(mask)

    return result


def collection_to_atlas(collection: ee.ImageCollection, 
                        xmin, xmax, ymin, ymax,
                        index:str='system:index', 
                        visParams:dict={}, 
                        width:int = 200, 
                        margin:float = 0,
                        transparent_bg:bool = False,
                        layout_name:str = "atlas-layout",
                        poly_name:str="atlas-bounds",
                        layer_attr:str = "image", 
                        )->None:
    """Loads images from a collection into the Map and prepares a Layout with Atlas, useful for exporting images.

    - Loads each image into the Map 
    - Prepares one Map theme for each image, in which only the given image is visible.
    - Loads a vector Polygon named `poly_name` with a rectangular geometry (xmin, xmax, ymin, ymax).
      The vector Polygon has a single `layer_attr` which will refer to each image 
      in the collection by `index`.
    - Prepares a Layout named `layout_name` in the Project.
    - A QgsLayoutItemMap with dimensions `width` x `width` is created in the Layout.
    - The QgsLayoutItemMap is set to be controlled by Atlas. 
      The dimension of the QgsLayoutItemMap will be adjusted based on the dimensions of the
      rectangular bound, and the margin around the atlas feature extent. 
    - The filename for each image is set to "@atlas_pagename", 
       while `atlas_pagename` is set to `layer_attr` = `index`. That is, the file name will be 
       set to the selected index for the ee.ImageCollection (the default is `system:index`).
     
    To export the images: open the Layout, click on "Atlas" (top menu), and then "Export Atlas as Images".

    Arguments:
        collection: The ee.ImageCollection 
        xmin, xmax, ymin, ymax: The rectangular extent to be set to the Map in the Layout.
        index: name of a unique index to identify each ee.Image. Defaults to "system:index"
        visParams: Visualization parameters. Defaults to {}
        width: Width (in millimeters) for the Map in the Layout. 
        margin: Margin (%) around the extent to leave blank in the Map within the Layout. 
        transparent_bg: Whether to make the background transparent. 
        layout_name: Name of the Layout created in the Project. Defaults to "atlas-layout"
        poly_name: Name of the Vector Polygon that is created in the Map. Defaults to "atlas-bounds"
        layer_attr: Name of the attribute to create in the vector Polygon. Defaults to "image" 
    
    Example:

    ```python
    import ee
    from ee_plugin.contrib import utils

    ee.Initialize()

    collection = (ee.ImageCollection('MODIS/061/MOD13A3')
            .filterDate('2023-01-01', '2023-05-01')
            .select('NDVI')
            .map(lambda img: img.divide(10000))
    )
    visParams = {
      'min': 0,
      'max': 1,
      'palette': [
        'ffffff', 'ce7e45', 'df923d', 'f1b555', 'fcd163', '99b718', '74a901',
        '66a000', '529400', '3e8601', '207401', '056201', '004c00', '023b01',
        '012e01', '011d01', '011301'
      ],
    }

    w, e, s, n = -85, -30, -43, 15
    utils.collection_to_atlas(collection, xmin=w, xmax = e, ymin=s, ymax= n, visParams = visParams)
    ```

    """
    import qgis.core
    from qgis.utils import iface
    from PyQt5.QtCore import QVariant
    from PyQt5.QtGui import QColor 
    from qgis.core import (QgsProject, QgsVectorLayer, QgsPointXY, 
                           QgsFeature, QgsGeometry, QgsField, 
                           QgsPrintLayout, QgsLayoutItemMap,
                           QgsLayoutSize, QgsUnitTypes,
                           QgsProperty,
                           )
    from ee_plugin.utils import add_or_update_ee_layer, get_layer_by_name

    project = QgsProject.instance()
    manager = project.layoutManager()

    layout = None
    map = None

    layouts = manager.layouts()
    for L in layouts:
       if L.name()==layout_name:
          layout = L
          break

    if not layout:
        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        layout.setName(layout_name)
        manager.addLayout(layout)

    for item in layout.items():
       if isinstance(item, QgsLayoutItemMap):
          map = item
          break

    if not map:
        map = QgsLayoutItemMap(layout)
        layout.addLayoutItem(map)

    pages = layout.pageCollection()
    page = pages.page(0)
    map.attemptResize(QgsLayoutSize(width, width, QgsUnitTypes.LayoutMillimeters))
    map.setAtlasMargin(margin)
    if transparent_bg:
       page.setOpacity(0)
       map.setBackgroundColor(QColor(0,0,0,0))

    polyLayer =  QgsVectorLayer('Polygon', poly_name , "memory")
    pr = polyLayer.dataProvider() 
    pr.addAttributes([QgsField(layer_attr, QVariant.String)]) 
    polyLayer.updateFields()
    bounds = [[xmin,ymax], [xmax,ymax], [xmax,ymin], [xmin,ymin]]
    points = [QgsPointXY(*pt) for pt in bounds]
    
    featList = []

    image_list = collection.toList(collection.size())
    n = collection.size().getInfo()

    for i in list(range(n)):
        image = ee.Image(image_list.get(i))
        name = str(image.get(index).getInfo())

        feat = QgsFeature(polyLayer.fields())
        feat.setGeometry(QgsGeometry.fromPolygonXY([points]))
        feat.setAttributes([name])  
        featList.append(feat)

        add_or_update_ee_layer(image, visParams, name, shown=True, opacity=1.0)

        mapTheme = qgis.core.QgsMapThemeCollection.createThemeFromCurrentState(
            project.layerTreeRoot(),
            iface.layerTreeView().layerTreeModel()
        )
        project.mapThemeCollection().insert(name, mapTheme)

        layer = get_layer_by_name(name)
        project.layerTreeRoot().findLayer(
        layer.id()).setItemVisibilityChecked(False)

    pr.addFeatures(featList)
    p_layer = get_layer_by_name(poly_name)
    if p_layer:
        project.removeMapLayers( [p_layer.id()] )
    
    project.addMapLayers([polyLayer])

    atlas = layout.atlas()
    atlas.setEnabled(True)
    atlas.setHideCoverage(True)
    atlas.setCoverageLayer(polyLayer)
    atlas.setPageNameExpression(layer_attr)
    atlas.setFilenameExpression("@atlas_pagename")

    map.setAtlasDriven(True)
    map.setFollowVisibilityPreset(True)
    map.dataDefinedProperties().setProperty(QgsLayoutItemMap.MapStylePreset, 
        QgsProperty.fromExpression(layer_attr))
