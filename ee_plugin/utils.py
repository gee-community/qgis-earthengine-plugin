# -*- coding: utf-8 -*-
"""
Utils functions for EE
"""

from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt, QCoreApplication

import os
import math
import json
import tempfile
import logging
from typing import Optional, TypedDict, Tuple, Any, List

try:
    import gzip

    _GZIP_AVAILABLE = True
except ImportError:
    _GZIP_AVAILABLE = False

import ee
import qgis
import requests
from osgeo import gdal
from qgis.core import (
    QgsProcessingFeedback,
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsMapLayer,
    QgsRectangle,
    QgsCoordinateReferenceSystem,
    QgsProcessingContext,
    QgsCoordinateTransform,
    QgsWkbTypes,
    QgsSimpleMarkerSymbolLayer,
    QgsSimpleLineSymbolLayer,
    QgsSimpleFillSymbolLayer,
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Change as needed (DEBUG/INFO/WARNING/ERROR)

EE_LAYER_PROPERTY = "ee-layer"
EE_LAYER_TYPE_PROPERTY = "ee-layer-type"
EE_OBJECT_PROPERTY = "ee-object"
EE_OBJECT_VIS_PROPERTY = "ee-object-vis"
EE_ASSET_ID_PROPERTY = "ee-asset-id"

# --- Encoding-size helpers (module-level; used by tile_extent) ---


def _bytes_for_data_type(dt: dict) -> int:
    """Best-effort bytes-per-sample from EE band data_type metadata.
    EE returns { 'precision': 'int'|'float'|'double', 'min': ..., 'max': ... }.
    We infer width from precision and/or min/max when present. Defaults to 2 bytes.
    """
    if not isinstance(dt, dict):
        return 2
    precision = dt.get("precision")
    if precision == "double":
        return 8
    if precision == "float":
        return 4
    if precision == "int":
        minv = dt.get("min")
        maxv = dt.get("max")
        if isinstance(minv, (int, float)) and isinstance(maxv, (int, float)):
            # 8-bit ranges
            if (0 <= minv <= 255 and 0 <= maxv <= 255) or (
                -128 <= minv <= 127 and -128 <= maxv <= 127
            ):
                return 1
            # 16-bit ranges
            if (0 <= minv <= 65535 and 0 <= maxv <= 65535) or (
                -32768 <= minv <= 32767 and -32768 <= maxv <= 32767
            ):
                return 2
            # Otherwise assume 32-bit int
            return 4
        # No bounds: default typical int16
        return 2
    # Unknown precision: conservative default
    return 2


def estimate_bytes_per_pixel(img: ee.Image) -> int:
    """Estimate bytes-per-pixel for an EE image by summing per-band sizes.
    Falls back to band_count * 2 when metadata is missing.
    Adds one byte for the mask to match Earth Engine’s accounting.
    """
    ee_mask_bytes = 1
    try:
        info = img.getInfo()
        bands_info = info.get("bands", []) if isinstance(info, dict) else []
        if bands_info:
            return sum(
                _bytes_for_data_type(band.get("data_type", {})) + ee_mask_bytes
                for band in bands_info
            )
    except Exception as e:
        logger.debug(f"Could not read band data types from getInfo(): {e}")
    try:
        n_bands = img.bandNames().size().getInfo()
        return int(n_bands) * (2 + ee_mask_bytes)
    except Exception as e:
        logger.debug(f"Could not read band count; defaulting to 2 bytes-per-pixel: {e}")
        return 2 + ee_mask_bytes


filter_functions = {
    "==": {"operator": ee.Filter.eq, "symbol": "=="},
    "!=": {"operator": ee.Filter.neq, "symbol": "!="},
    "<": {"operator": ee.Filter.lt, "symbol": "<"},
    ">": {"operator": ee.Filter.gt, "symbol": ">"},
    "<=": {"operator": ee.Filter.lte, "symbol": "<="},
    ">=": {"operator": ee.Filter.gte, "symbol": ">="},
}


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
    try:
        table_id = eeObject.args.get("tableId", "")
        return bool(table_id)
    except AttributeError:
        logger.debug("EE Object has no tableId attribute.")
        return False


def get_layer_by_name(name: str) -> Optional[QgsMapLayer]:
    iface = getattr(qgis.utils, "iface", None)
    if iface:
        canvas_layers = [
            layer for layer in iface.mapCanvas().layers() if layer.name() == name
        ]
        logger.debug(f"Found {len(canvas_layers)} canvas layers with name '{name}'.")
        if canvas_layers:
            return canvas_layers[0]

    layers = QgsProject.instance().mapLayersByName(name)
    logger.debug(f"Found {len(layers)} project layer(s) with name '{name}'.")
    return layers[0] if layers else None


def get_ee_raster_layers() -> list[QgsMapLayer]:
    iface = getattr(qgis.utils, "iface", None)
    canvas_layer_ids = set()
    raster_layers = []

    if iface:
        for layer in iface.mapCanvas().layers():
            if is_ee_raster_layer(layer):
                raster_layers.append(layer)
                canvas_layer_ids.add(layer.id())

    for layer in QgsProject.instance().mapLayers().values():
        if is_ee_raster_layer(layer) and layer.id() not in canvas_layer_ids:
            raster_layers.append(layer)

    return raster_layers


def get_ee_image_url(image: ee.Image) -> str:
    map_id = ee.data.getMapId({"image": image})
    url = map_id["tile_fetcher"].url_format
    logger.debug(f"Generated EE image URL: {url}")
    return url


def set_layer_extent_from_ee_object(
    layer: QgsMapLayer, ee_object: ee.Element, warning_context: str
) -> None:
    try:
        bounds = ee_object.geometry().bounds().getInfo()["coordinates"][0]
        xs = [pt[0] for pt in bounds]
        ys = [pt[1] for pt in bounds]
        rect = QgsRectangle(min(xs), min(ys), max(xs), max(ys))
        layer.setExtent(rect)
    except Exception as e:
        logger.warning(f"Could not set {warning_context} from ee_object: {e}")


def _serialize_ee_object(ee_object: ee.Element) -> str:
    return ee.serializer.toJSON(ee_object)


def set_ee_layer_properties(
    layer: QgsMapLayer,
    ee_object: ee.Element,
    vis_params: Optional[VisualizeParams] = None,
    layer_type: str = "raster",
) -> None:
    layer.setCustomProperty(EE_LAYER_PROPERTY, True)
    layer.setCustomProperty(EE_LAYER_TYPE_PROPERTY, layer_type)
    layer.setCustomProperty(EE_OBJECT_PROPERTY, _serialize_ee_object(ee_object))
    layer.setCustomProperty(EE_OBJECT_VIS_PROPERTY, json.dumps(vis_params or {}))
    try:
        asset_id = ee_object.id().getInfo() if hasattr(ee_object, "id") else None
    except Exception:
        asset_id = None
    if asset_id:
        layer.setCustomProperty(EE_ASSET_ID_PROPERTY, asset_id)


def is_ee_layer(layer: QgsMapLayer) -> bool:
    return bool(layer and layer.customProperty(EE_LAYER_PROPERTY))


def is_ee_raster_layer(layer: QgsMapLayer) -> bool:
    return bool(
        is_ee_layer(layer) and layer.customProperty(EE_LAYER_TYPE_PROPERTY) == "raster"
    )


def get_ee_object_from_layer(layer: QgsMapLayer) -> Optional[ee.Element]:
    if not is_ee_layer(layer):
        return None
    serialized = layer.customProperty(EE_OBJECT_PROPERTY)
    if serialized:
        try:
            return ee.deserializer.fromJSON(serialized)
        except Exception as e:
            logger.warning(
                f"Could not deserialize ee object from layer {layer.name()}: {e}"
            )
    provider_object = getattr(layer.dataProvider(), "ee_object", None)
    return provider_object


def add_or_update_ee_layer(
    eeObject: ee.Element,
    vis_params: VisualizeParams,
    name: str,
    shown: bool,
    opacity: float,
) -> QgsMapLayer:
    logger.info(f"Adding/updating EE layer: {name}")
    if isinstance(eeObject, ee.Image):
        layer = add_or_update_ee_raster_layer(
            eeObject, name, vis_params, shown, opacity
        )
    elif isinstance(eeObject, ee.FeatureCollection):
        if is_named_dataset(eeObject):
            layer = add_or_update_named_vector_layer(
                eeObject, name, vis_params, shown, opacity
            )
        else:
            layer = add_or_update_ee_vector_layer(
                eeObject, name, vis_params, shown, opacity
            )
    elif isinstance(eeObject, ee.Geometry):
        layer = add_or_update_ee_vector_layer(
            eeObject, name, vis_params, shown, opacity
        )
    elif isinstance(eeObject, ee.ImageCollection):
        reduce_image = eeObject.reduce(ee.Reducer.median())
        layer = add_or_update_ee_raster_layer(reduce_image, name, vis_params, shown)
    else:
        raise TypeError("Unsupported EE object type")

    # Set extent from eeObject geometry
    try:
        bounds = eeObject.geometry().bounds().getInfo()["coordinates"][0]
        xs = [pt[0] for pt in bounds]
        ys = [pt[1] for pt in bounds]
        rect4326 = QgsRectangle(min(xs), min(ys), max(xs), max(ys))

        crs_src = QgsCoordinateReferenceSystem("EPSG:4326")
        crs_dest = QgsCoordinateReferenceSystem("EPSG:3857")
        xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
        rect3857 = xform.transform(rect4326)

        layer.setExtent(rect3857)
    except Exception as e:
        logger.warning(f"Could not set extent from eeObject: {e}")

    return layer


def add_or_update_ee_raster_layer(
    image: ee.Image,
    name: str,
    vis_params: VisualizeParams,
    shown: bool = True,
    opacity: float = 1.0,
) -> QgsRasterLayer:
    logger.debug(f"Adding/updating EE raster layer: {name}")
    layer = get_layer_by_name(name)
    if layer and is_ee_layer(layer):
        return update_ee_image_layer(image, layer, vis_params, shown, opacity)
    return add_ee_image_layer(image, name, vis_params, shown, opacity)


def add_ee_image_layer(
    image: ee.Image,
    name: str,
    vis_params: VisualizeParams,
    shown: bool,
    opacity: float,
) -> QgsRasterLayer:
    logger.debug(f"Adding EE image layer: {name}")
    check_version()
    url = "type=xyz&url=" + get_ee_image_url(image.visualize(**vis_params))
    layer = QgsRasterLayer(url, name, "wms")
    assert layer.isValid(), f"Failed to load layer: {name}"
    set_ee_layer_properties(layer, image, vis_params, layer_type="raster")
    QgsProject.instance().addMapLayer(layer)

    if opacity is not None and layer.renderer():
        layer.renderer().setOpacity(opacity)

    return layer


def update_ee_image_layer(
    image: ee.Image,
    layer: QgsMapLayer,
    vis_params: VisualizeParams,
    shown: bool = True,
    opacity: float = 1.0,
) -> QgsRasterLayer:
    logger.debug(f"Updating EE image layer: {layer.name()}")
    check_version()
    url = "type=xyz&url=" + get_ee_image_url(image.visualize(**vis_params))
    layer.setDataSource(url, layer.name(), "wms")
    assert layer.isValid(), f"Failed to update layer: {layer.name()}"
    set_ee_layer_properties(layer, image, vis_params, layer_type="raster")

    if opacity is not None and layer.renderer():
        layer.renderer().setOpacity(opacity)

    if shown is not None:
        layer_node = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
        if layer_node:
            layer_node.setItemVisibilityChecked(shown)

    layer.triggerRepaint()
    return layer


def add_or_update_named_vector_layer(
    eeObject: ee.Element,
    name: str,
    vis_params: VisualizeParams,
    shown: bool = True,
    opacity: float = 1.0,
) -> QgsRasterLayer:
    logger.debug(f"Adding/updating named EE vector layer: {name}")
    table_id = eeObject.args.get("tableId", "")
    if not table_id:
        raise ValueError(f"FeatureCollection {name} does not have a valid tableId.")
    # Keys accepted by FeatureCollection.style() on the EE server side.
    # Client-side-only keys (lineColor, polygonFillColor, etc.) are silently
    # dropped here; they only take effect on the local vector path.
    ee_style_keys = {
        "color",
        "fillColor",
        "width",
        "pointSize",
        "pointShape",
        "lineType",
    }
    if vis_params and any(k in vis_params for k in ee_style_keys):
        style_kwargs = {k: v for k, v in vis_params.items() if k in ee_style_keys}
        image = eeObject.style(**style_kwargs)
        # Style is already baked into the image; don't pass vis_params again
        return add_or_update_ee_raster_layer(image, name, {}, shown, opacity)
    else:
        image = ee.Image().paint(eeObject, 0, 2)
        return add_or_update_ee_raster_layer(image, name, {}, shown, opacity)


def add_or_update_ee_vector_layer(
    eeObject: ee.Element,
    name: str,
    vis_params: Optional[dict] = None,
    shown: bool = True,
    opacity: float = 1.0,
) -> QgsVectorLayer:
    logger.debug(f"Adding/updating EE vector layer: {name}")
    layer = get_layer_by_name(name)
    if layer:
        if not layer.customProperty("ee-layer"):
            raise Exception(f"Layer is not an EE layer: {name}")
        return update_ee_vector_layer(eeObject, layer, vis_params, shown, opacity)
    return add_ee_vector_layer(eeObject, name, vis_params, shown, opacity)


def _geometry_type(name: str):
    geometry_type = getattr(QgsWkbTypes, "GeometryType", QgsWkbTypes)
    return getattr(geometry_type, name)


def _constant_style_value(style_params: dict, key: str):
    value = style_params.get(key)
    if isinstance(value, dict):
        logger.warning(
            f"Data-driven style property '{key}' is not supported for QGIS vector layers; ignoring."
        )
        return None
    return value


def _numeric_style_value(style_params: dict, key: str) -> Optional[float]:
    value = _constant_style_value(style_params, key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        logger.warning(
            f"Invalid numeric value '{value}' for style property '{key}', ignoring."
        )
        return None


def _convert_line_type(line_type: str) -> Qt.PenStyle:
    if not isinstance(line_type, str):
        logger.warning(f"Invalid line type '{line_type}', falling back to solid.")
        return Qt.PenStyle.SolidLine
    mapping = {
        "solid": Qt.PenStyle.SolidLine,
        "dashed": Qt.PenStyle.DashLine,
        "dotted": Qt.PenStyle.DotLine,
    }
    return mapping.get(line_type.lower(), Qt.PenStyle.SolidLine)


def _get_marker_shape(shape_name: str):
    if not isinstance(shape_name, str):
        logger.warning(f"Invalid point shape '{shape_name}', falling back to circle.")
        shape_name = "circle"
    name = shape_name.lower()
    try:
        shape_cls = QgsSimpleMarkerSymbolLayer.Shape
        mapping = {
            "circle": shape_cls.Circle,
            "square": shape_cls.Square,
            "diamond": shape_cls.Diamond,
            "triangle": shape_cls.Triangle,
            "triangle_up": shape_cls.Triangle,
            "cross": shape_cls.Cross,
            "plus": shape_cls.Cross2,
            "pentagon": shape_cls.Pentagon,
            "hexagon": shape_cls.Hexagon,
            "star5": shape_cls.Star,
            "star6": shape_cls.Star,
            "pentagram": shape_cls.Star,
            "hexagram": shape_cls.Star,
        }
        if name not in mapping:
            logger.warning(
                f"Unknown point shape '{shape_name}', falling back to circle. "
                f"Known shapes: {list(mapping.keys())}"
            )
        return mapping.get(name, shape_cls.Circle)
    except AttributeError:
        mapping = {
            "circle": QgsSimpleMarkerSymbolLayer.Circle,
            "square": QgsSimpleMarkerSymbolLayer.Square,
            "diamond": QgsSimpleMarkerSymbolLayer.Diamond,
            "triangle": QgsSimpleMarkerSymbolLayer.Triangle,
            "triangle_up": QgsSimpleMarkerSymbolLayer.Triangle,
            "cross": QgsSimpleMarkerSymbolLayer.Cross,
            "plus": QgsSimpleMarkerSymbolLayer.Cross2,
            "pentagon": QgsSimpleMarkerSymbolLayer.Pentagon,
            "hexagon": QgsSimpleMarkerSymbolLayer.Hexagon,
            "star5": QgsSimpleMarkerSymbolLayer.Star,
            "star6": QgsSimpleMarkerSymbolLayer.Star,
            "pentagram": QgsSimpleMarkerSymbolLayer.Star,
            "hexagram": QgsSimpleMarkerSymbolLayer.Star,
        }
        if name not in mapping:
            logger.warning(
                f"Unknown point shape '{shape_name}', falling back to circle. "
                f"Known shapes: {list(mapping.keys())}"
            )
        return mapping.get(name, QgsSimpleMarkerSymbolLayer.Circle)


def _qcolor(value) -> Optional[QColor]:
    if not isinstance(value, str):
        logger.warning(f"Invalid color value '{value}', ignoring.")
        return None
    color_value = value.strip()
    if not color_value.startswith("#") and len(color_value) in (3, 6, 8):
        try:
            int(color_value, 16)
            color_value = f"#{color_value}"
        except ValueError:
            pass
    color = QColor(color_value)
    if color.isValid():
        return color
    logger.warning(f"Invalid color value '{value}', ignoring.")
    return None


def _apply_vector_style(layer: QgsVectorLayer, style_params: dict) -> None:
    renderer = layer.renderer()
    if not renderer or not renderer.symbol():
        return

    symbol = renderer.symbol()
    symbol_layer = symbol.symbolLayer(0)
    if not symbol_layer:
        return

    geometry_type = layer.geometryType()

    base_color = _constant_style_value(style_params, "color")
    base_fill_color = _constant_style_value(style_params, "fillColor") or base_color

    opacity = _numeric_style_value(style_params, "opacity")
    if geometry_type == _geometry_type("PointGeometry"):
        point_opacity = _numeric_style_value(style_params, "pointFillOpacity")
        if point_opacity is not None:
            opacity = point_opacity
    elif geometry_type == _geometry_type("LineGeometry"):
        line_opacity = _numeric_style_value(style_params, "lineOpacity")
        if line_opacity is not None:
            opacity = line_opacity
    elif geometry_type == _geometry_type("PolygonGeometry"):
        stroke_opacity = _numeric_style_value(style_params, "polygonStrokeOpacity")
        fill_opacity = _numeric_style_value(style_params, "polygonFillOpacity")
        if stroke_opacity is not None:
            opacity = stroke_opacity
        elif fill_opacity is not None:
            opacity = fill_opacity

    if opacity is not None:
        symbol.setOpacity(opacity)

    if geometry_type == _geometry_type("PointGeometry"):
        fill_color = (
            _constant_style_value(style_params, "pointFillColor") or base_fill_color
        )
        stroke_color = base_color
        size = _numeric_style_value(style_params, "pointSize")
        shape = _constant_style_value(style_params, "pointShape")
        stroke_width = _numeric_style_value(style_params, "width")

        if isinstance(symbol_layer, QgsSimpleMarkerSymbolLayer):
            if fill_color:
                color = _qcolor(fill_color)
                if color:
                    symbol_layer.setColor(color)
            if stroke_color:
                color = _qcolor(stroke_color)
                if color:
                    symbol_layer.setStrokeColor(color)
            if stroke_width is not None:
                symbol_layer.setStrokeWidth(stroke_width)
            if size is not None:
                symbol_layer.setSize(size)
            if shape:
                symbol_layer.setShape(_get_marker_shape(shape))

    elif geometry_type == _geometry_type("LineGeometry"):
        line_color = _constant_style_value(style_params, "lineColor") or base_color
        line_width = _numeric_style_value(style_params, "lineWidth")
        if line_width is None:
            line_width = _numeric_style_value(style_params, "width")
        line_type = _constant_style_value(style_params, "lineType")

        if isinstance(symbol_layer, QgsSimpleLineSymbolLayer):
            if line_color:
                color = _qcolor(line_color)
                if color:
                    symbol_layer.setColor(color)
            if line_width is not None:
                symbol_layer.setWidth(line_width)
            if line_type:
                symbol_layer.setPenStyle(_convert_line_type(line_type))

    elif geometry_type == _geometry_type("PolygonGeometry"):
        stroke_color = (
            _constant_style_value(style_params, "polygonStrokeColor") or base_color
        )
        fill_color = (
            _constant_style_value(style_params, "polygonFillColor") or base_fill_color
        )
        stroke_width = _numeric_style_value(style_params, "polygonStrokeWidth")
        if stroke_width is None:
            stroke_width = _numeric_style_value(style_params, "width")
        stroke_type = _constant_style_value(style_params, "polygonStrokeType")

        if isinstance(symbol_layer, QgsSimpleFillSymbolLayer):
            if stroke_color:
                color = _qcolor(stroke_color)
                if color:
                    symbol_layer.setStrokeColor(color)
            if fill_color:
                color = _qcolor(fill_color)
                if color:
                    symbol_layer.setFillColor(color)
            if stroke_width is not None:
                symbol_layer.setStrokeWidth(stroke_width)
            if stroke_type:
                symbol_layer.setStrokeStyle(_convert_line_type(stroke_type))

    from qgis.utils import iface

    iface.layerTreeView().refreshLayerSymbology(layer.id())


def _ee_object_to_geojson(eeObject: ee.Element) -> dict:
    info = eeObject.getInfo()

    if info["type"] == "FeatureCollection":
        return {
            "type": "FeatureCollection",
            "features": info["features"],
        }
    elif info["type"] == "Feature":
        return {
            "type": "FeatureCollection",
            "features": [info],
        }
    elif info["type"] in (
        "Polygon",
        "MultiPolygon",
        "Point",
        "LineString",
        "MultiLineString",
        "LinearRing",
    ):
        return {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "geometry": info, "properties": {}}],
        }
    else:
        raise ValueError("Unsupported EE object type: " + info["type"])


def _write_geojson_temp_file(geojson: dict) -> str:
    # Use gzip by default; fall back to plain .geojson if unavailable
    compress = _GZIP_AVAILABLE
    suffix = ".geojson.gz" if compress else ".geojson"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.close()  # close the fd so we can reopen it
    if compress:
        with gzip.open(temp_file.name, "wt", encoding="utf-8") as f:
            json.dump(geojson, f)
    else:
        with open(temp_file.name, "w") as f:
            json.dump(geojson, f)
    return temp_file.name


def _cleanup_vector_source_path(path: Optional[str]) -> None:
    if not path:
        return
    try:
        os.remove(path)
        logger.debug(f"Cleaned up old vector source: {path}")
    except PermissionError:
        logger.warning(f"Could not remove old vector source (file locked): {path}")
    except OSError as e:
        logger.warning(f"Could not remove old vector source: {path} — {e}")


def add_ee_vector_layer(
    eeObject: ee.Element,
    name: str,
    vis_params: Optional[dict] = None,
    shown: bool = True,
    opacity: float = 1.0,
) -> QgsVectorLayer:
    logger.debug(f"Adding EE vector layer: {name}")
    geojson = _ee_object_to_geojson(eeObject)
    uri = _write_geojson_temp_file(geojson)
    layer = QgsVectorLayer(uri, name, "ogr")
    assert layer.isValid(), f"Failed to load vector layer: {name}"
    set_ee_layer_properties(layer, eeObject, vis_params or {}, layer_type="vector")

    QgsProject.instance().addMapLayer(layer)
    layer.setCustomProperty("ee-layer", True)
    layer.setCustomProperty("ee-vector-source", uri)

    if shown is not None:
        tree_layer = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
        if tree_layer:
            tree_layer.setItemVisibilityChecked(shown)
        else:
            logger.warning(
                "Layer not found in layer tree when trying to set visibility."
            )

    renderer = layer.renderer()
    if renderer and renderer.symbol() and opacity is not None:
        renderer.symbol().setOpacity(opacity)

    if vis_params:
        _apply_vector_style(layer, vis_params)

    return layer


def update_ee_vector_layer(
    eeObject: ee.Element,
    layer: QgsMapLayer,
    vis_params: Optional[dict] = None,
    shown: bool = True,
    opacity: float = 1.0,
) -> QgsVectorLayer:
    logger.debug(f"Updating EE vector layer: {layer.name()}")
    geojson = _ee_object_to_geojson(eeObject)
    uri = _write_geojson_temp_file(geojson)
    old_source = layer.customProperty("ee-vector-source")
    layer.setDataSource(uri, layer.name(), "ogr")
    assert layer.isValid(), f"Failed to reload vector layer: {layer.name()}"

    _cleanup_vector_source_path(old_source)
    set_ee_layer_properties(layer, eeObject, vis_params or {}, layer_type="vector")
    layer.setCustomProperty("ee-vector-source", uri)
    renderer = layer.renderer()
    if renderer and renderer.symbol() and opacity is not None:
        renderer.symbol().setOpacity(opacity)

    if vis_params:
        _apply_vector_style(layer, vis_params)

    if shown is not None:
        tree_node = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
        if tree_node:
            tree_node.setItemVisibilityChecked(shown)

    return layer


def add_ee_catalog_image(
    name: str, asset_name: str, vis_params: VisualizeParams
) -> QgsRasterLayer:
    logger.debug(f"Adding EE catalog image: {name}")
    image = ee.Image(asset_name).visualize(**vis_params)
    return add_or_update_ee_raster_layer(image, name, vis_params)


def check_version() -> None:
    qgis.utils.plugins["ee_plugin"].check_version()


def translate(message: str) -> str:
    return QCoreApplication.translate("GoogleEarthEngine", message)


def ee_image_to_geotiff(
    ee_image: ee.Image,
    extent: Tuple[float, float, float, float],
    scale: float,
    projection: str,
    out_dir: str = "/vsimem/",
    base_name: str = "tiles_",
    merge_output: Optional[str] = None,
    feedback: Optional[QgsProcessingFeedback] = None,
) -> None:
    logger.info(
        f"Exporting EE image to GeoTIFF with scale {scale}, projection {projection}"
    )
    os.makedirs(out_dir, exist_ok=True)

    logger.debug(f"Provided extent for export: {extent}")

    tiles = tile_extent(ee_image, extent, scale, projection)
    logger.info(f"Generated {len(tiles)} tiles for export.")

    # hard-coded early warning for large number of tiles
    if len(tiles) > 5:
        logger.warning(
            "Exporting large number of tiles. Consider reducing scale or extent."
        )
    tile_paths = []

    if feedback is not None:
        try:
            feedback.pushInfo("Preparing export…")
            feedback.setProgress(0)
        except Exception:
            pass

    with tempfile.TemporaryDirectory() as temp_dir:
        n_tiles = len(tiles)
        for idx, tile in enumerate(tiles):
            if feedback and feedback.isCanceled():
                logger.info("Export cancelled by user.")
                return
            # Progress update inside loop, proportional to idx/n_tiles (0–100)
            pct = int((idx / n_tiles) * 100) if n_tiles > 0 else 0
            if feedback is not None:
                try:
                    feedback.setProgress(pct)
                    feedback.pushInfo(f"Downloading tile {idx + 1}/{n_tiles}…")
                except Exception:
                    pass
            out_path = os.path.join(temp_dir, f"{base_name}_tile{idx}.tif")
            logger.info(f"Downloading tile {idx + 1}/{n_tiles} to {out_path}")
            download_tile(
                ee_image, tile, scale, projection, out_path, feedback=feedback
            )
            tile_paths.append(out_path)
        logger.info(f"Merging {len(tile_paths)} tiles into {merge_output}")
        if feedback and feedback.isCanceled():
            logger.info("Export cancelled by user before merge.")
            return

        if feedback is not None:
            try:
                feedback.setProgress(90)
                feedback.pushInfo("Merging tiles…")
            except Exception:
                pass

        merge_geotiffs_gdal(tile_paths, merge_output)

        if feedback is not None:
            try:
                feedback.setProgress(100)
                feedback.pushInfo("Merging tiles complete.")
            except Exception:
                pass


def merge_geotiffs_gdal(in_files: List[str], out_file: str) -> None:
    logger.info(f"Merging files into {out_file}")
    out_type = out_file.split(".")[-1]

    if out_type == "vrt":
        vrt = gdal.BuildVRT(out_file, in_files)
        vrt = None
    else:
        vrt = gdal.BuildVRT("/vsimem/temp.vrt", in_files)
        gdal.Translate(
            out_file,
            vrt,
            options=gdal.TranslateOptions(
                format="COG",
                creationOptions=[
                    "COMPRESS=DEFLATE",
                    "TILING=YES",
                    "BLOCKXSIZE=512",
                    "BLOCKYSIZE=512",
                ],
            ),
        )
        vrt = None


def validate_extent_projection(
    extent: Tuple[float, float, float, float], projection: str
) -> None:
    """
    Validate that the extent coordinates match the expected projection.
    For EPSG:4326, coordinates should be in degrees (longitude, latitude).
    For EPSG:3857, coordinates should be in meters.
    """
    if projection == "EPSG:4326":
        if not (-180 <= extent[0] <= 180 and -90 <= extent[1] <= 90):
            raise ValueError("Extent coordinates are out of bounds for EPSG:4326.")
    elif projection == "EPSG:3857":
        if not (
            -20037508.34 <= extent[0] <= 20037508.34
            and -20037508.34 <= extent[1] <= 20037508.34
        ):
            raise ValueError("Extent coordinates are out of bounds for EPSG:3857.")


def tile_extent(
    ee_image: ee.Image,
    extent: Tuple[float, float, float, float],
    scale: float,
    projection: str = "EPSG:4326",
) -> List[Tuple[float, float, float, float]]:
    logger.debug(f"Tiling extent {extent} with scale {scale}, projection {projection}")

    logger.debug(f"Validating extent projection for {projection}")
    validate_extent_projection(extent, projection)

    bytes_per_pixel = estimate_bytes_per_pixel(ee_image)
    max_bytes = 30 * 1024 * 1024
    if bytes_per_pixel <= 0:
        bytes_per_pixel = 2
    max_pixels = max_bytes // bytes_per_pixel

    xmin, ymin, xmax, ymax = extent
    width = xmax - xmin
    height = ymax - ymin

    tile_side = math.sqrt(max_pixels) * scale

    # If using geographic coordinates, convert tile side from meters to degrees
    tile_width = tile_height = (
        tile_side / 111_320 if projection == "EPSG:4326" else tile_side
    )
    if projection == "EPSG:4326":
        tile_width = tile_side / 111320
        tile_height = tile_width
    else:
        tile_width = tile_side
        tile_height = tile_side

    tiles_x = math.ceil(width / tile_width)
    tiles_y = math.ceil(height / tile_height)

    logger.debug(
        f"Tile width: {tile_width}, Tile height: {tile_height}, Tiles in X: {tiles_x}, Tiles in Y: {tiles_y}"
    )

    tiles = []
    for i in range(tiles_x):
        for j in range(tiles_y):
            tile_xmin = xmin + i * tile_width
            tile_xmax = min(tile_xmin + tile_width, xmax)
            tile_ymin = ymin + j * tile_height
            tile_ymax = min(tile_ymin + tile_height, ymax)
            tiles.append((tile_xmin, tile_ymin, tile_xmax, tile_ymax))

    logger.debug(f"Created {len(tiles)} tile(s).")
    return tiles


def download_tile(
    ee_image: ee.Image,
    tile_extent: Tuple[float, float, float, float],
    scale: float,
    projection: str,
    out_path: str,
    feedback: Optional[QgsProcessingFeedback] = None,
) -> None:
    logger.debug(
        f"Downloading tile {tile_extent} with scale {scale}, projection {projection}"
    )
    ee_proj = ee.Projection(projection)
    region_geom = ee.Geometry.Rectangle(tile_extent, proj=ee_proj, geodesic=False)
    # Transform region to EPSG:4326 before getting bounds
    region_geom_wgs84 = region_geom.transform("EPSG:4326", maxError=1)
    region_coords = region_geom_wgs84.bounds(maxError=1).getInfo()["coordinates"][0]

    download_params = {
        "image": ee_image,
        "scale": scale,
        "crs": projection,
        "region": region_coords,
        "format": "GEO_TIFF",
    }

    download_id = ee.data.getDownloadId(download_params)
    url = ee.data.makeDownloadUrl(download_id)

    # Stream the response so we can honor cancellation promptly
    with requests.get(url, stream=True, timeout=(10, 120)) as resp:
        resp.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 512):  # 512 KB
                if feedback is not None and feedback.isCanceled():
                    logger.info(
                        "Cancel detected during tile download; removing partial file."
                    )
                    try:
                        f.close()
                    finally:
                        try:
                            if os.path.exists(out_path):
                                os.remove(out_path)
                        except Exception:
                            pass
                    return
                if not chunk:
                    continue
                f.write(chunk)
    logger.debug(f"Tile saved to {out_path}")


def get_ee_properties(asset_id: str, silent: bool = False) -> Optional[List[str]]:
    """
    Get property names from any Earth Engine asset.
    """
    try:
        asset = ee.data.getAsset(asset_id)

        if asset["type"] == "IMAGE_COLLECTION":
            obj = ee.ImageCollection(asset_id).first()
        elif asset["type"] == "IMAGE":
            obj = ee.Image(asset_id)
        elif asset["type"] == "FEATURE_COLLECTION":
            obj = ee.FeatureCollection(asset_id).first()
        elif asset["type"] == "TABLE":
            obj = ee.FeatureCollection(asset_id).first()
        else:
            if not silent:
                logger.warning(f"Unhandled EE object type: {asset['type']!r}")
            return None

        props = obj.toDictionary().getInfo()
        return sorted(props.keys())
    except Exception:
        if not silent:
            logger.exception(f"Error retrieving properties from asset {asset_id!r}")
        return None


def get_available_bands(
    asset_id: str,
    silent: bool = False,
) -> Optional[List[str]]:
    """
    Get available bands from an Earth Engine image or image collection.
    """
    try:
        asset = ee.data.getAsset(asset_id)

        if asset["type"] == "IMAGE_COLLECTION":
            obj = ee.ImageCollection(asset_id).first()
        elif asset["type"] == "IMAGE":
            obj = ee.Image(asset_id)
        else:
            if not silent:
                logger.warning(f"Unhandled EE object type: {asset['type']!r}")
            return None

        bands = obj.bandNames().getInfo()
        return sorted(bands)
    except Exception:
        if not silent:
            logger.exception(f"Error retrieving bands from asset {asset_id!r}")
        return None


def get_ee_extent(
    extent: QgsRectangle,
    extent_crs: QgsCoordinateReferenceSystem,
    context: QgsProcessingContext,
) -> ee.Geometry:
    """
    Convert a QGIS extent and CRS to an Earth Engine Geometry which must always be in EPSG:4326.
    The extent is expected to be in the same CRS as the provided extent_crs.
    """
    crs_4326 = QgsCoordinateReferenceSystem("EPSG:4326")
    transform = QgsCoordinateTransform(extent_crs, crs_4326, context)

    extent_4326 = transform.transform(extent)
    ee_extent = ee.Geometry.Rectangle(
        [
            extent_4326.xMinimum(),
            extent_4326.yMinimum(),
            extent_4326.xMaximum(),
            extent_4326.yMaximum(),
        ]
    )

    return ee_extent


def parse_extent_string(extent_str: str) -> QgsRectangle:
    """Parse strings like "xmin,xmax,ymin,ymax [EPSG:xxxx]" to a QgsRectangle.
    QGIS bookmarks / model extents often come in this order (x min, x max, y min, y max).
    """
    try:
        # Remove optional CRS suffix like " [EPSG:4326]"
        core = extent_str.split("[")[0].strip()
        parts = [p.strip() for p in core.split(",")]
        if len(parts) != 4:
            raise ValueError("Expected four comma-separated numbers")
        xmin, xmax, ymin, ymax = map(float, parts)
        return QgsRectangle(xmin, ymin, xmax, ymax)
    except Exception as e:
        raise ValueError(f"Could not parse extent string: {extent_str}") from e


def normalize_crs(crs, project) -> QgsCoordinateReferenceSystem:
    """Return a valid QgsCoordinateReferenceSystem from various inputs.
    Accepts: QgsCoordinateReferenceSystem, 'ProjectCrs', 'project', 'EPSG:xxxx', WKT, PROJ string.
    Falls back to the current project CRS when appropriate.
    """
    if isinstance(crs, QgsCoordinateReferenceSystem):
        if crs.isValid():
            return crs
    if crs is None or crs == "" or str(crs).lower() in ("projectcrs", "project"):
        return project.crs()
    # Try to parse arbitrary string input
    try:
        crs_obj = QgsCoordinateReferenceSystem.fromUserInput(str(crs))
        if crs_obj.isValid():
            return crs_obj
    except Exception:
        pass
    raise ValueError(f"Invalid extent CRS: {crs}")
