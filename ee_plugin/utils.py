# -*- coding: utf-8 -*-
"""
Utils functions GEE
"""

import json
import tempfile

import ee
import qgis
from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer
from .ee_plugin import VERSION as ee_plugin_version


def get_layer_by_name(name):
    layers = QgsProject.instance().mapLayers().values()

    for layer in layers:
        if layer.name() == name:
            return layer

    return None


def get_ee_image_url(image):
    map_id = ee.data.getMapId({"image": image})
    url = map_id["tile_fetcher"].url_format + "&zmax=25"
    return url


def update_ee_layer_properties(layer, eeObject, opacity):
    """
    Updates the layer properties including opacity.
    """
    layer.dataProvider().set_ee_object(eeObject)
    layer.setCustomProperty("ee-layer", True)

    if opacity is not None and layer.renderer():
        renderer = layer.renderer()
        if renderer:
            renderer.setOpacity(opacity)

    # Serialize EE object
    layer.setCustomProperty("ee-plugin-version", ee_plugin_version)
    layer.setCustomProperty("ee-object", eeObject.serialize())


def add_or_update_ee_layer(eeObject, vis_params, name, shown, opacity):
    """
    Entry point to add/update an EE layer. Routes between raster and vector layers.
    """
    if isinstance(eeObject, ee.Image):
        add_or_update_ee_raster_layer(eeObject, name, vis_params, shown, opacity)
    elif isinstance(
        eeObject, (ee.Geometry, ee.Feature, ee.ImageCollection, ee.FeatureCollection)
    ):
        add_or_update_ee_vector_layer(eeObject, name, shown, opacity)
    else:
        raise TypeError("Unsupported EE object type")


def add_or_update_ee_raster_layer(image, name, vis_params, shown=True, opacity=1.0):
    """
    Adds or updates a raster EE layer.
    """
    layer = get_layer_by_name(name)

    if layer and layer.customProperty("ee-layer"):
        layer = update_ee_image_layer(image, layer, vis_params, shown, opacity)
    else:
        layer = add_ee_image_layer(image, name, vis_params, shown, opacity)

    return layer


def add_ee_image_layer(image, name, vis_params, shown, opacity):
    """
    Adds a raster layer using the 'EE' provider.
    """
    check_version()
    url = "type=xyz&url=" + get_ee_image_url(image.visualize(**vis_params))

    layer = QgsRasterLayer(url, name, "EE")
    assert layer.isValid(), f"Failed to load layer: {name}"

    provider = layer.dataProvider()
    assert provider is not None, f"Failed to get provider for layer: {name}"

    layer.dataProvider().set_ee_object(image)
    qgis_instance = QgsProject.instance()

    qgis_instance.addMapLayer(layer)

    if opacity is not None and layer.renderer():
        layer.renderer().setOpacity(opacity)

    if shown is not None:
        qgis_instance.layerTreeRoot().findLayer(layer.id()).setItemVisibilityChecked(
            shown
        )

    return layer


def update_ee_image_layer(image, layer, vis_params, shown=True, opacity=1.0):
    """
    Updates an existing EE raster layer.
    """
    check_version()
    url = "type=xyz&url=" + get_ee_image_url(image.visualize(**vis_params))

    qgis_instance = QgsProject.instance()
    root = qgis_instance.layerTreeRoot()
    layer_node = root.findLayer(layer.id())
    parent_group = layer_node.parent()
    idx = parent_group.children().index(layer_node)

    new_layer = QgsRasterLayer(url, layer.name(), "EE")

    if opacity is not None and new_layer.renderer():
        new_layer.renderer().setOpacity(opacity)

    # Replace the old layer
    qgis_instance.removeMapLayers([layer.id()])
    qgis_instance.addMapLayer(new_layer, False)
    root.insertLayer(idx, new_layer)

    if shown is not None:
        root.findLayer(new_layer.id()).setItemVisibilityChecked(shown)

    return new_layer


def add_or_update_ee_vector_layer(eeObject, name, shown=True, opacity=1.0):
    """
    Handles vector layers by converting them to a properly styled GeoJSON vector layer.
    """
    layer = get_layer_by_name(name)

    if layer:
        if not layer.customProperty("ee-layer"):
            raise Exception(f"Layer is not an EE layer: {name}")
        layer = update_ee_vector_layer(eeObject, layer, shown, opacity)
    else:
        layer = add_ee_vector_layer(eeObject, name, shown, opacity)

    return layer


def add_ee_vector_layer(eeObject, name, shown=True, opacity=1.0):
    """
    Adds a vector layer properly by converting EE Geometry to a valid GeoJSON FeatureCollection.
    """
    # Convert EE geometry into a proper GeoJSON FeatureCollection
    geometry_info = eeObject.getInfo()
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": geometry_info,
                "properties": {},  # Empty properties
            }
        ],
    }

    # Write to a temporary file for QGIS
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".geojson")
    with open(temp_file.name, "w") as f:
        json.dump(geojson, f)

    # Use the temp file as the data source
    uri = temp_file.name

    # Create the vector layer
    layer = QgsVectorLayer(uri, name, "ogr")

    if not layer.isValid():
        print(f"Failed to load vector layer: {name}")
    else:
        QgsProject.instance().addMapLayer(layer)
        if shown is not None:
            QgsProject.instance().layerTreeRoot().findLayer(
                layer.id()
            ).setItemVisibilityChecked(shown)
        if opacity is not None and layer.renderer():
            symbol = layer.renderer().symbol()
            symbol.setOpacity(opacity)
            layer.triggerRepaint()

    return layer


def update_ee_vector_layer(eeObject, layer, shown, opacity):
    """
    Updates an existing vector layer with new features from EE.
    """
    geojson = eeObject.getInfo()
    uri = f"GeoJSON?crs=EPSG:4326&url={json.dumps(geojson)}"

    new_layer = QgsVectorLayer(uri, layer.name(), "ogr")

    QgsProject.instance().removeMapLayers([layer.id()])
    QgsProject.instance().addMapLayer(new_layer)

    if opacity is not None and layer.renderer():
        new_layer.renderer().setOpacity(opacity)

    if shown is not None:
        QgsProject.instance().layerTreeRoot().findLayer(
            new_layer.id()
        ).setItemVisibilityChecked(shown)

    return new_layer


def add_ee_catalog_image(name, asset_name, vis_params):
    """
    Adds an EE image from a catalog.
    """
    image = ee.Image(asset_name).visualize(vis_params)
    add_or_update_ee_raster_layer(image, name)


def check_version():
    """
    Check if we have the latest plugin version.
    """
    qgis.utils.plugins["ee_plugin"].check_version()
