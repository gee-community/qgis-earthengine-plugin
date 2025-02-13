# -*- coding: utf-8 -*-
"""
Utils functions GEE
"""

import json
import tempfile
from typing import Optional, TypedDict, Any

import ee
import qgis
from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer, QgsMapLayer
from qgis.PyQt.QtCore import QCoreApplication


class VisualizeParams(TypedDict, total=False):
    bands: Optional[Any]
    gain: Optional[Any]
    bias: Optional[Any]
    min: Optional[Any]
    max: Optional[Any]
    gamma: Optional[Any]
    opacity: Optional[float]
    palette: Optional[Any]
    forceRgbOutput: Optional[bool]


def is_named_dataset(eeObject: ee.Element) -> bool:
    """
    Checks if the FeatureCollection is a named dataset that should be handled as a vector tiled layer.
    """
    try:
        table_id = eeObject.args.get("tableId", "")
        return bool(table_id)  # If tableId exists, it's a named dataset
    except AttributeError:
        return False


def get_layer_by_name(name: str) -> Optional[QgsMapLayer]:
    for layer in QgsProject.instance().mapLayersByName(name):
        return layer


def get_ee_image_url(image: ee.Image) -> str:
    map_id = ee.data.getMapId({"image": image})
    url = map_id["tile_fetcher"].url_format + "&zmax=25"
    return url


def add_or_update_ee_layer(
    eeObject: ee.Element,
    vis_params: VisualizeParams,
    name: str,
    shown: bool,
    opacity: float,
) -> QgsMapLayer:
    """
    Entry point to add/update an EE layer. Routes between raster, vector layers, and vector tile layers.
    """
    if isinstance(eeObject, ee.Image):
        return add_or_update_ee_raster_layer(eeObject, name, vis_params, shown, opacity)

    if isinstance(eeObject, ee.FeatureCollection):
        if is_named_dataset(eeObject):
            return add_or_update_named_vector_layer(
                eeObject, name, vis_params, shown, opacity
            )
        return add_or_update_ee_vector_layer(eeObject, name, shown, opacity)

    if isinstance(eeObject, ee.Geometry):
        return add_or_update_ee_vector_layer(eeObject, name, shown, opacity)

    raise TypeError("Unsupported EE object type")


def add_or_update_ee_raster_layer(
    image: ee.Image,
    name: str,
    vis_params: VisualizeParams,
    shown: bool = True,
    opacity: float = 1.0,
) -> QgsRasterLayer:
    """
    Adds or updates a raster EE layer.
    """
    layer = get_layer_by_name(name)

    if layer and layer.customProperty("ee-layer"):
        return update_ee_image_layer(image, layer, vis_params, shown, opacity)

    return add_ee_image_layer(image, name, vis_params, shown, opacity)


def add_ee_image_layer(
    image: ee.Image,
    name: str,
    vis_params: VisualizeParams,
    shown: bool,
    opacity: float,
) -> QgsRasterLayer:
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


def update_ee_image_layer(
    image: ee.Image,
    layer: QgsMapLayer,
    vis_params: VisualizeParams,
    shown: bool = True,
    opacity: float = 1.0,
) -> QgsRasterLayer:
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


def add_or_update_named_vector_layer(
    eeObject: ee.Element,
    name: str,
    vis_params: VisualizeParams,
    shown: bool = True,
    opacity: float = 1.0,
) -> QgsRasterLayer:
    """
    Adds or updates a vector tiled layer from an Earth Engine named dataset.
    """
    table_id = eeObject.args.get("tableId", "")
    if not table_id:
        raise ValueError(f"FeatureCollection {name} does not have a valid tableId.")

    # Given the potential large-size of named datasets, we render FeatureCollections as WMS raster layers
    image = ee.Image().paint(eeObject, 0, 2)

    return add_or_update_ee_raster_layer(image, name, vis_params, shown, opacity)


def add_or_update_ee_vector_layer(
    eeObject: ee.Element,
    name: str,
    shown: bool = True,
    opacity: float = 1.0,
) -> QgsVectorLayer:
    """
    Handles vector layers by converting them to a properly styled GeoJSON vector layer.
    """
    layer = get_layer_by_name(name)

    if layer:
        if not layer.customProperty("ee-layer"):
            raise Exception(f"Layer is not an EE layer: {name}")
        return update_ee_vector_layer(eeObject, layer, shown, opacity)

    return add_ee_vector_layer(eeObject, name, shown, opacity)


def add_ee_vector_layer(
    eeObject: ee.Element,
    name: str,
    shown: bool = True,
    opacity: float = 1.0,
) -> QgsVectorLayer:
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


def update_ee_vector_layer(
    eeObject: ee.Element,
    layer: QgsMapLayer,
    shown: bool,
    opacity: float,
) -> QgsVectorLayer:
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


def add_ee_catalog_image(
    name: str,
    asset_name: str,
    vis_params: VisualizeParams,
) -> QgsRasterLayer:
    """
    Adds an EE image from a catalog.
    """
    image = ee.Image(asset_name).visualize(**vis_params)
    add_or_update_ee_raster_layer(image, name)


def check_version() -> None:
    """
    Check if we have the latest plugin version.
    """
    qgis.utils.plugins["ee_plugin"].check_version()


def translate(message: str) -> str:
    """
    Helper to translate messages.
    """
    return QCoreApplication.translate("GoogleEarthEngine", message)
