# -*- coding: utf-8 -*-
"""
Utils functions GEE
"""

import json

import ee
import qgis
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsPointXY,
    QgsProject,
    QgsRasterLayer,
    QgsRectangle,
)

import ee_plugin


def get_ee_image_url(image):
    map_id = ee.data.getMapId({"image": image})
    url = map_id["tile_fetcher"].url_format + "&zmax=25"
    return url


def update_ee_layer_properties(layer, eeObject, visParams, shown, opacity):
    layer.dataProvider().set_ee_object(eeObject)

    layer.setCustomProperty("ee-layer", True)

    if opacity is not None:
        renderer = layer.renderer()
        if renderer:
            renderer.setOpacity(opacity)

    # serialize EE code
    ee_object = eeObject.serialize()
    ee_object_vis = json.dumps(visParams)
    layer.setCustomProperty("ee-plugin-version", ee_plugin.ee_plugin.VERSION)
    layer.setCustomProperty("ee-object", ee_object)
    layer.setCustomProperty("ee-object-vis", ee_object_vis)

    # update EE script in provider
    if eeObject.getInfo()["type"] == "Image":  # TODO
        layer.dataProvider().set_ee_object(eeObject)


def add_ee_image_layer(image, name, shown, opacity):
    check_version()

    url = "type=xyz&url=" + get_ee_image_url(image)

    # EE raster data provider
    if image.ee_type == ee.Image:
        layer = QgsRasterLayer(url, name, "EE")
    # EE vector data provider
    if image.ee_type in [ee.Geometry, ee.Feature]:
        # TODO
        layer = QgsRasterLayer(url, name, "wms")
    # EE raster collection data provider
    if image.ee_type == ee.ImageCollection:
        # TODO
        layer = QgsRasterLayer(url, name, "wms")
    # EE vector collection data provider
    if image.ee_type == ee.FeatureCollection:
        # TODO
        layer = QgsRasterLayer(url, name, "wms")

    QgsProject.instance().addMapLayer(layer)

    if shown is not None:
        QgsProject.instance().layerTreeRoot().findLayer(
            layer.id()
        ).setItemVisibilityChecked(shown)

    return layer


def update_ee_image_layer(image, layer, shown=True, opacity=1.0):
    check_version()

    url = "type=xyz&url=" + get_ee_image_url(image)

    root = QgsProject.instance().layerTreeRoot()
    layer_node = root.findLayer(layer)  # layer is a QgsMapLayer
    parent_group = layer_node.parent()

    # Get layer index
    idx = parent_group.children().index(layer_node)

    # new layer
    layer_new = QgsRasterLayer(url, layer.name(), "EE")

    # Remove old layer
    QgsProject.instance().removeMapLayers([layer.id()])

    QgsProject.instance().addMapLayer(layer_new, False)
    root.insertLayer(idx, layer_new)

    layer = layer_new

    item = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
    if shown is not None:
        item.setItemVisibilityChecked(shown)

    return layer


def get_layer_by_name(name):
    layers = QgsProject.instance().mapLayers().values()

    for layer in layers:
        if layer.name() == name:
            return layer

    return None


def add_or_update_ee_layer(eeObject, visParams, name, shown, opacity):
    if visParams is None:
        visParams = {}

    if isinstance(eeObject, ee.Image):
        image = eeObject.visualize(**visParams)

    elif isinstance(
        eeObject, (ee.Geometry, ee.Feature, ee.ImageCollection, ee.FeatureCollection)
    ):
        features = ee.FeatureCollection(eeObject)

        if "width" in visParams:
            width = visParams["width"]
        else:
            width = 2

        if "color" in visParams:
            color = visParams["color"]
        else:
            color = "000000"

        image_fill = features.style(**{"fillColor": color}).updateMask(
            ee.Image.constant(0.5)
        )
        image_outline = features.style(
            **{"color": color, "fillColor": "00000000", "width": width}
        )

        image = image_fill.blend(image_outline)

    else:
        err_str = (
            "\n\nThe image argument in 'addLayer' function must be an instance of one of ee.Image, ee.Geometry, "
            "ee.Feature, ee.ImageCollection or ee.FeatureCollection."
        )
        raise AttributeError(err_str)

    if name is None:
        # extract name from id
        try:
            name = json.loads(eeObject.id().serialize())["scope"][0][1]["arguments"][
                "id"
            ]
        except (AttributeError, KeyError, IndexError, json.JSONDecodeError) as e:
            print(f"Error extracting name from id: {e}")
            name = "untitled"

    image.ee_type = type(eeObject)

    layer = add_or_update_ee_image_layer(image, name, shown, opacity)
    update_ee_layer_properties(layer, eeObject, visParams, shown, opacity)


def add_or_update_ee_image_layer(image, name, shown=True, opacity=1.0):
    layer = get_layer_by_name(name)

    if layer:
        if not layer.customProperty("ee-layer"):
            raise Exception("Layer is not an EE layer: " + name)

        layer = update_ee_image_layer(image, layer, shown, opacity)
    else:
        layer = add_ee_image_layer(image, name, shown, opacity)

    return layer


def add_ee_catalog_image(name, asset_name, visParams, collection_props):
    image = None

    if collection_props:
        raise Exception("Not supported yet")
    else:
        image = ee.Image(asset_name).visualize(visParams)

    add_or_update_ee_image_layer(image, name)


def check_version():
    # check if we have the latest version only once plugin is used, not once it is loaded
    qgis.utils.plugins["ee_plugin"].check_version()


def geom_to_geo(geom):
    crs_src = QgsCoordinateReferenceSystem(QgsProject.instance().crs())
    crs_dst = QgsCoordinateReferenceSystem("EPSG:4326")
    proj2geo = QgsCoordinateTransform(crs_src, crs_dst, QgsProject.instance())

    if isinstance(geom, QgsPointXY):
        return proj2geo.transform(geom)
    elif isinstance(geom, QgsRectangle):
        return proj2geo.transformBoundingBox(geom)
    else:
        return geom.transform(proj2geo)
