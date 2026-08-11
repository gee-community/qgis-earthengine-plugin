"""Fetch, cache, and search Earth Engine catalog metadata."""

import csv
import json
import os
from dataclasses import asdict, dataclass
from typing import Iterable, List, Optional
from urllib.request import Request, urlopen

from qgis.PyQt.QtCore import QStandardPaths


OFFICIAL_CATALOG_TSV_URL = (
    "https://raw.githubusercontent.com/opengeos/Earth-Engine-Catalog/master/"
    "gee_catalog.tsv"
)


@dataclass
class CatalogItem:
    title: str
    asset_id: str
    asset_type: str
    source: str = "Official Earth Engine Catalog"
    provider: str = ""
    category: str = ""
    keywords: Optional[List[str]] = None
    start_date: str = ""
    end_date: str = ""
    url: str = ""
    catalog_url: str = ""
    license: str = ""

    def __post_init__(self):
        self.keywords = self.keywords or []

    @property
    def search_text(self) -> str:
        return " ".join(
            [
                self.title,
                self.asset_id,
                self.asset_type,
                self.source,
                self.provider,
                self.category,
                " ".join(self.keywords),
            ]
        ).lower()


def cache_path() -> str:
    try:
        cache_location = QStandardPaths.StandardLocation.CacheLocation
    except AttributeError:
        cache_location = QStandardPaths.CacheLocation
    base_dir = QStandardPaths.writableLocation(cache_location)
    if not base_dir:
        base_dir = os.path.expanduser("~/.cache/qgis-earthengine-plugin")
    path = os.path.join(base_dir, "catalog")
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, "official_catalog.json")


def load_catalog(refresh: bool = False) -> List[CatalogItem]:
    path = cache_path()
    if not refresh and os.path.exists(path):
        return _items_from_cache(path)

    try:
        items = fetch_official_catalog()
    except Exception:
        if os.path.exists(path):
            return _items_from_cache(path)
        raise

    with open(path, "w", encoding="utf-8") as file_obj:
        json.dump([asdict(item) for item in items], file_obj)
    return items


def fetch_official_catalog() -> List[CatalogItem]:
    request = Request(
        OFFICIAL_CATALOG_TSV_URL,
        headers={"User-Agent": "QGIS-EarthEngine-Plugin"},
    )
    with urlopen(request, timeout=30) as response:  # nosec B310
        text = response.read().decode("utf-8")
    return parse_official_catalog_tsv(text)


def parse_official_catalog_tsv(text: str) -> List[CatalogItem]:
    reader = csv.DictReader(text.splitlines(), delimiter="\t")
    items = []
    for row in reader:
        if str(row.get("deprecated", "")).lower() == "true":
            continue
        asset_id = row.get("id", "").strip()
        title = row.get("title", "").strip()
        if not asset_id or not title:
            continue

        items.append(
            CatalogItem(
                title=title,
                asset_id=asset_id,
                asset_type=_normalize_asset_type(row.get("type", "")),
                provider=row.get("provider", "").strip(),
                category=row.get("category", "").strip(),
                keywords=_split_keywords(row.get("keywords", "")),
                start_date=row.get("state_date", "").strip(),
                end_date=row.get("end_date", "").strip(),
                url=row.get("url", "").strip(),
                catalog_url=row.get("catalog", "").strip(),
                license=row.get("license", "").strip(),
            )
        )
    return items


def search_catalog(
    items: Iterable[CatalogItem],
    query: str = "",
    asset_type: Optional[str] = None,
) -> List[CatalogItem]:
    query = query.strip().lower()
    asset_type = (asset_type or "").strip()
    filtered = [
        item
        for item in items
        if (not asset_type or item.asset_type == asset_type)
        and (not query or query in item.search_text)
    ]
    return sorted(filtered, key=lambda item: _rank_item(item, query))


def _items_from_cache(path: str) -> List[CatalogItem]:
    with open(path, encoding="utf-8") as file_obj:
        data = json.load(file_obj)
    return [CatalogItem(**item) for item in data]


def _normalize_asset_type(raw_type: str) -> str:
    raw_type = raw_type.strip().lower()
    if raw_type in ("image_collection", "imagecollection"):
        return "ImageCollection"
    if raw_type in ("table", "feature_collection", "featurecollection"):
        return "FeatureCollection"
    if raw_type == "image":
        return "Image"
    return raw_type or "Unknown"


def _split_keywords(value: str) -> List[str]:
    return [keyword.strip() for keyword in value.split(",") if keyword.strip()]


def _rank_item(item: CatalogItem, query: str) -> tuple:
    if not query:
        return (0, item.title.lower())
    if item.asset_id.lower() == query or item.title.lower() == query:
        rank = 0
    elif item.asset_id.lower().startswith(query) or item.title.lower().startswith(
        query
    ):
        rank = 1
    elif query in item.asset_id.lower() or query in item.title.lower():
        rank = 2
    else:
        rank = 3
    return (rank, item.title.lower())
