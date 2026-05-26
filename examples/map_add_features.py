import ee

from ee_plugin import Map

# ── How style keys are applied ────────────────────────────────────────────────
# The plugin uses two different rendering paths depending on the object type,
# and each path supports a different set of style keys:
#
# LOCAL VECTOR PATH  — used for ee.Geometry objects, and for FeatureCollections
#   that have been filtered or transformed (e.g. .filter(), .filterBounds()).
#   The data is fetched once from EE and stored as a local GeoJSON layer in
#   QGIS. All client-side style keys are supported:
#     color, fillColor, width, opacity,
#     pointFillColor, pointFillOpacity, pointSize, pointShape,
#     lineColor, lineWidth, lineOpacity, lineType,
#     polygonStrokeColor, polygonStrokeWidth, polygonFillColor,
#     polygonFillOpacity, polygonStrokeType
#
# CATALOG TILE PATH  — used for a bare FeatureCollection loaded directly by
#   asset ID without any further EE operations (e.g.
#   ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")).
#   The collection is rendered server-side as an XYZ tile using
#   FeatureCollection.style(). Only the keys that .style() accepts work here:
#     color, fillColor, width, pointSize, pointShape, lineType
#   All other keys above are silently ignored on this path.
#   For anything beyond those six keys, call .style() yourself (see Example 7).
# ─────────────────────────────────────────────────────────────────────────────

# ── Example 1: Single feature (polygon) with basic color ──
# "color" sets both stroke and fill on the local vector path.
# It also works on the catalog tile path (it is a .style() key).
countries = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
country = countries.filter(ee.Filter.eq("country_na", "Ukraine"))
Map.addLayer(country, {"color": "orange"}, "feature_basic_color")

# ── Example 2: Polygon with fill and stroke ──
# "fillColor" and "width" work on both paths.
Map.addLayer(
    country,
    {
        "fillColor": "lightblue",
        "color": "darkblue",
        "width": 3,
    },
    "feature_fill_stroke",
)

# ── Example 3: Polygon with opacity ──
# "opacity" is a local vector path key only — it has no equivalent in
# FeatureCollection.style(). Works here because .filter() puts the collection
# on the local vector path.
Map.addLayer(
    country,
    {
        "fillColor": "green",
        "color": "darkgreen",
        "opacity": 0.4,
        "width": 2,
    },
    "feature_opacity",
)

# ── Example 4: Point features with shape and size ──
# .filter() puts cities on the local vector path, so all point-specific keys
# are available. "pointShape", "pointFillColor", "pointFillOpacity" are
# local-vector-only keys — they would be ignored on the catalog tile path.
# "pointSize", "color", and "width" also work on the catalog tile path.
cities = ee.FeatureCollection("FAO/GAUL/2015/level2").filter(
    ee.Filter.eq("ADM0_NAME", "Colombia")
)
Map.addLayer(
    cities,
    {
        "pointShape": "diamond",
        "pointSize": 10,
        "pointFillColor": "red",
        "pointFillOpacity": 0.8,
        "color": "darkred",
        "width": 2,
    },
    "points_styled",
)

# ── Example 5: Line features with dash patterns ──
# .filterBounds() and .filter() put some_rivers on the local vector path.
# "lineColor", "lineWidth", "lineOpacity" are local-vector-only keys.
# "lineType" also works on the catalog tile path.
rivers = ee.FeatureCollection("WWF/HydroSHEDS/v1/FreeFlowingRivers")
roi = ee.Geometry.Rectangle([-76, 2, -74, 6])
some_rivers = rivers.filterBounds(roi).filter(ee.Filter.lte("RIV_ORD", 5))
Map.addLayer(
    some_rivers,
    {
        "lineType": "dashed",
        "lineWidth": 1,
        "lineColor": "blue",
        "lineOpacity": 0.7,
    },
    "rivers_dashed",
)

# ── Example 6: Polygon geometry-specific keys ──
# These fine-grained polygon keys are local-vector-only — they are not
# accepted by FeatureCollection.style() and would be silently ignored on
# the catalog tile path.
Map.addLayer(
    country,
    {
        "polygonStrokeWidth": 4,
        "polygonStrokeColor": "purple",
        "polygonFillColor": "lavender",
        "polygonFillOpacity": 0.3,
    },
    "feature_polygon_specific",
)

# ── Example 7: Catalog FeatureCollection with server-side .style() ──
# A bare FeatureCollection loaded by asset ID (no filter or transform) goes
# through the catalog tile path and only accepts the six .style() keys.
# For any styling beyond those, call .style() on the server side yourself.
# The result of .style() is an ee.Image, so pass {} as vis_params.
styled_fc = countries.filter(ee.Filter.eq("country_na", "Germany")).style(
    **{"fillColor": "gold", "color": "darkgoldenrod", "width": 2}
)
Map.addLayer(styled_fc, {}, "feature_gee_styled")

# ── Set Map center using coordinates and zoom ──
Map.setCenter(31.472, 49.044, 6)
