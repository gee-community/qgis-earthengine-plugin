# -*- coding: utf-8 -*-
"""
Utils functions for EE
"""

from qgis.PyQt.QtGui import QColor

import os
import math
import json
import tempfile
import logging
from typing import Optional, TypedDict, Tuple, Any, List

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
)
from qgis.PyQt.QtCore import QCoreApplication


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Change as needed (DEBUG/INFO/WARNING/ERROR)

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
    """
    try:
        info = img.getInfo()
        bands_info = info.get("bands", []) if isinstance(info, dict) else []
        if bands_info:
            return sum(_bytes_for_data_type(b.get("data_type", {})) for b in bands_info)
    except Exception as e:
        logger.debug(f"Could not read band data types from getInfo(): {e}")
    try:
        n_bands = img.bandNames().size().getInfo()
        return int(n_bands) * 2
    except Exception as e:
        logger.debug(f"Could not read band count; defaulting to 2 bytes-per-pixel: {e}")
        return 2


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
    layers = QgsProject.instance().mapLayersByName(name)
    logger.debug(f"Found {len(layers)} layers with name '{name}'.")
    return layers[0] if layers else None


def get_ee_image_url(image: ee.Image) -> str:
    map_id = ee.data.getMapId({"image": image})
    url = map_id["tile_fetcher"].url_format + "&zmax=12&minzoom=5&cache=1"
    logger.debug(f"Generated EE image URL: {url}")
    return url


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
            layer = add_or_update_ee_vector_layer(eeObject, name, shown, opacity)
    elif isinstance(eeObject, ee.Geometry):
        layer = add_or_update_ee_vector_layer(eeObject, name, shown, opacity)
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
    logger.debug(f"Adding EE image layer: {name}")
    check_version()
    url = "type=xyz&url=" + get_ee_image_url(image.visualize(**vis_params))
    layer = QgsRasterLayer(url, name, "EE")
    # Set extent from ee_object geometry
    try:
        bounds = image.geometry().bounds().getInfo()["coordinates"][0]
        xs = [pt[0] for pt in bounds]
        ys = [pt[1] for pt in bounds]
        rect = QgsRectangle(min(xs), min(ys), max(xs), max(ys))
        layer.setExtent(rect)
    except Exception as e:
        logger.warning(f"Could not set layer extent from ee_object: {e}")
    assert layer.isValid(), f"Failed to load layer: {name}"
    layer.dataProvider().set_ee_object(image)
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
    qgis_instance = QgsProject.instance()
    root = qgis_instance.layerTreeRoot()
    layer_node = root.findLayer(layer.id())
    parent_group = layer_node.parent()
    idx = parent_group.children().index(layer_node)

    new_layer = QgsRasterLayer(url, layer.name(), "EE")

    if opacity is not None and new_layer.renderer():
        new_layer.renderer().setOpacity(opacity)

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
    logger.debug(f"Adding/updating named EE vector layer: {name}")
    table_id = eeObject.args.get("tableId", "")
    if not table_id:
        raise ValueError(f"FeatureCollection {name} does not have a valid tableId.")
    image = ee.Image().paint(eeObject, 0, 2)
    return add_or_update_ee_raster_layer(image, name, vis_params, shown, opacity)


def add_or_update_ee_vector_layer(
    eeObject: ee.Element,
    name: str,
    shown: bool = True,
    opacity: float = 1.0,
    style_params: Optional[dict] = None,
) -> QgsVectorLayer:
    logger.debug(f"Adding/updating EE vector layer: {name}")
    layer = get_layer_by_name(name)
    if layer:
        if not layer.customProperty("ee-layer"):
            raise Exception(f"Layer is not an EE layer: {name}")
        return update_ee_vector_layer(eeObject, layer, shown, opacity)
    return add_ee_vector_layer(eeObject, name, shown, opacity, style_params)


def add_ee_vector_layer(
    eeObject: ee.Element,
    name: str,
    shown: bool = True,
    opacity: float = 1.0,
    style_params: Optional[dict] = None,
) -> QgsVectorLayer:
    logger.debug(f"Adding EE vector layer: {name}")
    info = eeObject.getInfo()

    if info["type"] == "FeatureCollection":
        geojson = {
            "type": "FeatureCollection",
            "features": info["features"],
        }
    elif info["type"] == "Feature":
        geojson = {
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
        geojson = {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "geometry": info, "properties": {}}],
        }
    else:
        raise ValueError("Unsupported EE object type: " + info["type"])

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".geojson")
    with open(temp_file.name, "w") as f:
        json.dump(geojson, f)

    uri = temp_file.name
    layer = QgsVectorLayer(uri, name, "ogr")
    assert layer.isValid(), f"Failed to load vector layer: {name}"

    QgsProject.instance().addMapLayer(layer)

    if shown is not None:
        tree_layer = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
        if tree_layer:
            tree_layer.setItemVisibilityChecked(shown)
        else:
            logger.warning(
                "Layer not found in layer tree when trying to set visibility."
            )

    if style_params:
        symbol = layer.renderer().symbol()
        symbol_layer = symbol.symbolLayer(0)
        if style_params.get("opacity"):
            symbol.setOpacity(style_params["opacity"])
        if style_params.get("color"):
            symbol_layer.setStrokeColor(QColor(style_params["color"]))
        if style_params.get("width"):
            symbol_layer.setStrokeWidth(style_params["width"])
        if style_params.get("fillColor"):
            symbol_layer.setFillColor(QColor(style_params["fillColor"]))

    return layer


def update_ee_vector_layer(
    eeObject: ee.Element,
    layer: QgsMapLayer,
    shown: bool,
    opacity: float,
) -> QgsVectorLayer:
    logger.debug(f"Updating EE vector layer: {layer.name()}")
    geojson = eeObject.getInfo()
    uri = f"GeoJSON?crs=EPSG:4326&url={json.dumps(geojson)}"

    new_layer = QgsVectorLayer(uri, layer.name(), "ogr")
    QgsProject.instance().removeMapLayers([layer.id()])
    QgsProject.instance().addMapLayer(new_layer)

    if opacity is not None and new_layer.renderer():
        new_layer.renderer().setOpacity(opacity)

    if shown is not None:
        QgsProject.instance().layerTreeRoot().findLayer(
            new_layer.id()
        ).setItemVisibilityChecked(shown)

    return new_layer


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
