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
COMMUNITY_CATALOG_JSON_URL = (
    "https://raw.githubusercontent.com/samapriya/awesome-gee-community-datasets/"
    "master/community_datasets.json"
)

OFFICIAL_SOURCE = "Official Earth Engine Catalog"
COMMUNITY_SOURCE = "Awesome GEE Community Catalog"


@dataclass
class CatalogItem:
    title: str
    asset_id: str
    asset_type: str
    source: str = OFFICIAL_SOURCE
    provider: str = ""
    category: str = ""
    keywords: Optional[List[str]] = None
    start_date: str = ""
    end_date: str = ""
    url: str = ""
    catalog_url: str = ""
    license: str = ""
    license_text: str = ""
    sample_code_url: str = ""
    thumbnail_url: str = ""

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
                self.license,
                self.license_text,
                self.sample_code_url,
                " ".join(self.keywords),
            ]
        ).lower()


def cache_path() -> str:
    return os.path.join(cache_dir(), "catalog.json")


def cache_dir() -> str:
    try:
        cache_location = QStandardPaths.StandardLocation.CacheLocation
    except AttributeError:
        cache_location = QStandardPaths.CacheLocation
    base_dir = QStandardPaths.writableLocation(cache_location)
    if not base_dir:
        base_dir = os.path.expanduser("~/.cache/qgis-earthengine-plugin")
    path = os.path.join(base_dir, "catalog")
    os.makedirs(path, exist_ok=True)
    return path


def source_cache_path(source_name: str) -> str:
    filename = source_name.lower().replace(" ", "_") + ".json"
    return os.path.join(cache_dir(), filename)


def load_catalog(refresh: bool = False) -> List[CatalogItem]:
    path = cache_path()
    if not refresh and os.path.exists(path):
        return _items_from_cache(path)

    items = []
    items.extend(_load_catalog_source("official", fetch_official_catalog, refresh))
    items.extend(_load_catalog_source("community", fetch_community_catalog, refresh))

    if not items and os.path.exists(path):
        return _items_from_cache(path)
    if not items:
        raise RuntimeError("Could not load official or community catalog data.")

    with open(path, "w", encoding="utf-8") as file_obj:
        json.dump([asdict(item) for item in items], file_obj)
    return items


def _load_catalog_source(source_name: str, fetcher, refresh: bool) -> List[CatalogItem]:
    path = source_cache_path(source_name)
    if not refresh and os.path.exists(path):
        return _items_from_cache(path)

    try:
        items = fetcher()
    except Exception:
        if os.path.exists(path):
            return _items_from_cache(path)
        return []

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


def fetch_community_catalog() -> List[CatalogItem]:
    request = Request(
        COMMUNITY_CATALOG_JSON_URL,
        headers={"User-Agent": "QGIS-EarthEngine-Plugin"},
    )
    with urlopen(request, timeout=30) as response:  # nosec B310
        text = response.read().decode("utf-8")
    return parse_community_catalog_json(text)


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
                source=OFFICIAL_SOURCE,
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


def parse_community_catalog_json(text: str) -> List[CatalogItem]:
    records = json.loads(text)
    items = []
    for row in records:
        asset_id = _clean_value(row.get("id"))
        title = _clean_value(row.get("title"))
        if not asset_id or not title:
            continue

        items.append(
            CatalogItem(
                title=title,
                asset_id=asset_id,
                asset_type=_normalize_asset_type(_clean_value(row.get("type"))),
                source=COMMUNITY_SOURCE,
                provider=_clean_value(row.get("provider")),
                category=_clean_value(row.get("thematic_group")),
                keywords=_split_keywords(_clean_value(row.get("tags"))),
                url=_clean_value(row.get("docs")),
                license=_clean_value(row.get("license")),
                license_text=_clean_value(row.get("license_text")),
                sample_code_url=_clean_value(row.get("sample_code")),
                thumbnail_url=_clean_value(row.get("thumbnail")),
            )
        )
    return items


def search_catalog(
    items: Iterable[CatalogItem],
    query: str = "",
    asset_type: Optional[str] = None,
    source: Optional[str] = None,
    provider: Optional[str] = None,
    category: Optional[str] = None,
) -> List[CatalogItem]:
    query = query.strip().lower()
    asset_type = (asset_type or "").strip()
    source = (source or "").strip()
    provider = (provider or "").strip()
    category = (category or "").strip()
    filtered = [
        item
        for item in items
        if (not asset_type or item.asset_type == asset_type)
        and (not source or item.source == source)
        and (not provider or item.provider == provider)
        and (not category or item.category == category)
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


def _clean_value(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


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
