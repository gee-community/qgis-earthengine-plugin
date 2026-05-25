import ee

from ee_plugin import Map

# ── Example 1: Single feature (polygon) with basic color ──
# The "color" key sets the stroke color for polygon boundaries.
countries = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
country = countries.filter(ee.Filter.eq("country_na", "Ukraine"))
Map.addLayer(country, {"color": "orange"}, "feature_basic_color")

# ── Example 2: Polygon with fill and stroke ──
# "fillColor" controls interior color; "color" is the outline.
# "width" sets the outline width in pixels.
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
# "opacity" (0-1) controls both fill and stroke transparency.
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
# "pointShape" can be "circle", "square", "triangle", "diamond", etc.
# "pointSize" controls the diameter in pixels.
# "pointFillColor" and "pointFillOpacity" set the interior styling.
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
# "lineType" accepts "solid", "dashed", or "dotted".
# "lineWidth" and "lineColor" control the stroke appearance.
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

# ── Example 6: Polygon with separate stroke and fill opacity ──
# "polygonStrokeWidth", "polygonStrokeColor", "polygonFillColor", etc.
# allow fine-grained control of polygon appearance.
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

# ── Example 7: Using GEE .style() for data-driven visuals ──
# When a FeatureCollection has many features, call .style() on the
# server side and pass an empty visParams dict so the baked-in
# style is rendered directly in QGIS.
styled_fc = countries.filter(ee.Filter.eq("country_na", "Germany")).style(
    **{"fillColor": "gold", "color": "darkgoldenrod", "width": 2}
)
Map.addLayer(styled_fc, {}, "feature_gee_styled")

# ── Set Map center using coordinates and zoom ──
Map.setCenter(31.472, 49.044, 6)
