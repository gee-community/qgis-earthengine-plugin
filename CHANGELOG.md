# Changelog

All notable changes to this project will be documented in this file.

## [0.0.9] – 2025-07-03
### Added
- Interactive UI for Earth Engine authentication, replacing the previous manual flow.
- Support for styled visualization of image layers using custom palettes and opacity control.
- Enhanced **Add Feature Collection** algorithm with an option to retain layers as native QGIS vector data.
- New **Export GeoTIFF** tool for exporting Earth Engine imagery as Cloud-Optimized GeoTIFFs (COGs).

### Fixed
- Resolved import initialization error (`ModuleNotFoundError`) in the Python Console.
- Improved handling of expired Earth Engine authentication tokens — now prompts for re-authentication automatically.
- Optimized metadata loading and image collection querying for smoother performance.

### Changed
- Updated documentation (README, help files) with enhanced usage instructions and clearer code examples.
- Implemented `flake8` via pre-commit for consistent linting.
- Added CI packaging workflow with `.qgis-plugin-ci` configuration.

## [0.0.8] – 2025-05-16
*Experimental channel release*  [oai_citation:0‡github.com](https://github.com/gee-community/qgis-earthengine-plugin) [oai_citation:1‡gee-community.github.io](https://gee-community.github.io/qgis-earthengine-plugin/) [oai_citation:2‡developers.google.com](https://developers.google.com/earth-engine/docs/release-notes) [oai_citation:3‡plugins.qgis.org](https://plugins.qgis.org/plugins/ee_plugin/)  
### Changed
- Removed bundled `rasterio` extlibs to meet the 25 MB plugin size limit  [oai_citation:4‡github.com](https://github.com/gee-community/qgis-earthengine-plugin/issues/275).

## [0.0.7] – 2024-11-09
*Stable release* ()  
### Added / Changed
- Maintained compatibility with QGIS 3.22–3.99.
- Internal bug fixes and UI enhancements (unspecified public details).

## [0.0.6] – 2023-01-05
*Experimental release*  [oai_citation:5‡plugins.qgis.org](https://plugins.qgis.org/plugins/ee_plugin/)

## [0.0.5] – 2022-06-26
*Experimental release* ()

## [0.0.4] – 2021-03-29
*Experimental release* ()

## [0.0.3] – 2021-01-05
*Experimental release* ()

## [0.0.2] – 2020-06-22
*Experimental release* ()

## [0.0.1] – 2019-12-02
*Initial release* ()  
### Added
- First plugin release integrating Earth Engine, with basic image, vector loading, SRTM support, and authentication.