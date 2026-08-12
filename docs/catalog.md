---
title: Data Catalog
---

# Data Catalog

The Data Catalog lets you search for Earth Engine datasets from inside QGIS and load a selected asset into the plugin's existing add-layer dialogs.

Open it from **Plugins > Google Earth Engine > Data Catalog**. The catalog appears as a dockable panel in QGIS.

## Browse datasets

When the catalog opens, it loads the official Earth Engine catalog by default. Use the search box to search by dataset name, asset ID, provider, tags, license, or other metadata.

You can narrow results with these filters:

| Filter | Description |
| --- | --- |
| Type | Shows images, image collections, or feature collections. |
| Source | Switches between the official catalog, the community catalog, or all loaded sources. |
| Provider | Limits results to a specific dataset provider. |
| Category | Limits results to a catalog category or thematic group. |

The results table shows the dataset title, type, source, provider, category, and date range. Click a column heading to sort the table.

## View dataset details

Select a dataset to view its details. The details panel shows the asset ID, type, source, provider, category, date range, license, keywords, and available links.

Use the action buttons below the details panel to:

| Button | Action |
| --- | --- |
| Load | Opens the matching add-layer dialog with the selected asset ID filled in. |
| Copy Asset ID | Copies the asset ID to the clipboard. |
| Open Dataset Page | Opens the dataset documentation page in your browser when a link is available. |

Double-clicking a dataset also loads it.

## Load datasets

The **Load** action sends the selected asset to the correct plugin dialog:

| Dataset type | Dialog |
| --- | --- |
| Image | **Add Image** |
| ImageCollection | **Add Image Collection** |
| FeatureCollection | **Add Feature Collection** |

For image collections and feature collections, catalog start and end dates are applied to the dialog date filters when the catalog provides them. Review the dialog settings before adding the layer, especially visualization parameters, date filters, and geometry filters.

## Catalog sources

The **Official** source uses the Earth Engine dataset catalog metadata. This is the default source loaded when the panel opens.

The **Community** source loads datasets from the Awesome GEE Community Catalog. Community catalog entries are shown separately from official entries and may not be reviewed by Google. Check the linked dataset page, sample code, and license before using community datasets in a project.

Choose **All sources** to search across both sources. If the community catalog has not been loaded yet, selecting **Community** or **All sources** starts loading it.

## Refresh and cache

Catalog data is cached locally so the panel can reopen faster and continue working when a previously loaded source is temporarily unavailable. The cache is refreshed automatically after seven days.

Click **Refresh** to fetch fresh metadata for the currently selected source. If **Community** is selected, only the community catalog is refreshed. For **Official** or **All sources**, the official catalog is refreshed.

## Troubleshooting

If the catalog does not load, check that QGIS can access the internet and try **Refresh**. If the catalog has loaded before, the plugin will use cached data when a refresh fails.

If a dataset cannot be loaded, confirm that its type is supported by the plugin. The catalog can load images, image collections, and feature collections.
