import ee
from ee_plugin.contrib import utils

collection = (
    ee.ImageCollection("MODIS/061/MOD13A3")
    .filterDate("2023-01-01", "2023-05-01")
    .select("NDVI")
    .map(lambda img: img.divide(10000))
)
visParams = {
    "min": 0,
    "max": 1,
    "palette": [
        "ffffff",
        "ce7e45",
        "df923d",
        "f1b555",
        "fcd163",
        "99b718",
        "74a901",
        "66a000",
        "529400",
        "3e8601",
        "207401",
        "056201",
        "004c00",
        "023b01",
        "012e01",
        "011d01",
        "011301",
    ],
}

w, e, s, n = -85, -30, -43, 15  # Region of interest (rectangular bounds)
utils.collection_to_atlas(
    collection, xmin=w, xmax=e, ymin=s, ymax=n, visParams=visParams, transparent_bg=True
)
