# Changelog

All notable changes to this project will be documented in this file.

## [0.2.1](https://github.com/gee-community/qgis-earthengine-plugin/compare/v0.2.0...v0.2.1) (2026-07-02)


### Bug Fixes

* use QGIS token for plugin publishing ([54789c8](https://github.com/gee-community/qgis-earthengine-plugin/commit/54789c85274a1bf1ff11f90aa7f9dd1ef0a782ef))

## [0.2.0](https://github.com/gee-community/qgis-earthengine-plugin/compare/v0.1.8...v0.2.0) (2026-07-02)


### Features

* Add __version__.py and update check_version to use GitHub raw URL ([db75978](https://github.com/gee-community/qgis-earthengine-plugin/commit/db75978970b922691f7406bd7dc349b11a85f9fe))
* Add __version__.py and update check_version to use GitHub raw URL ([566ae93](https://github.com/gee-community/qgis-earthengine-plugin/commit/566ae9377671eecf787042e33b7a0ae85582666c))
* add Earth Engine identify tool ([#452](https://github.com/gee-community/qgis-earthengine-plugin/issues/452)) ([1e562db](https://github.com/gee-community/qgis-earthengine-plugin/commit/1e562db375a3456f656f19ade8848978c96f9422))
* vector visParams support and style ([#447](https://github.com/gee-community/qgis-earthengine-plugin/issues/447)) ([628c5ce](https://github.com/gee-community/qgis-earthengine-plugin/commit/628c5ced9c161baec0804c562c6be7a9cd43a560))


### Bug Fixes

* adjust deps for dev in requirements ([#445](https://github.com/gee-community/qgis-earthengine-plugin/issues/445)) ([b21e1d0](https://github.com/gee-community/qgis-earthengine-plugin/commit/b21e1d01968519f198610dc6afa0b02a39058dd3))
* avoid full refreshes for EE raster layers ([#442](https://github.com/gee-community/qgis-earthengine-plugin/issues/442)) ([8d2a76c](https://github.com/gee-community/qgis-earthengine-plugin/commit/8d2a76ca1993749de1b0ebd8dfe190195bb737d6))
* version comparison ([859b91c](https://github.com/gee-community/qgis-earthengine-plugin/commit/859b91c9e50b65577103c73e1c481f57939174e5))

## [0.1.8](https://github.com/gee-community/qgis-earthengine-plugin/compare/v0.1.7...v0.1.8) (2026-05-05)


### Bug Fixes

* make pkg_resources optional for QGIS 3.44 compatibility ([#426](https://github.com/gee-community/qgis-earthengine-plugin/issues/426)) ([b4dea0b](https://github.com/gee-community/qgis-earthengine-plugin/commit/b4dea0b3dc2c960e5ccc22088adea2556dd8dfc4))

## [0.1.7](https://github.com/gee-community/qgis-earthengine-plugin/compare/v0.1.6...v0.1.7) (2026-01-10)


### Bug Fixes

* add gee tag to metadata.txt ([#421](https://github.com/gee-community/qgis-earthengine-plugin/issues/421)) ([1a038c5](https://github.com/gee-community/qgis-earthengine-plugin/commit/1a038c55f4a150dd48ab2854fcb5cb437acf9952))

## [0.1.6](https://github.com/gee-community/qgis-earthengine-plugin/compare/v0.1.5...v0.1.6) (2025-12-04)


### Bug Fixes

* Pin the earthengine-api to a specific version to ensure Python compatibility ([88d4c76](https://github.com/gee-community/qgis-earthengine-plugin/commit/88d4c76a3e54bfae974e5ddc9da8cb63eb3b7736))
* pin the earthengine-api to a specific version to ensure Python version compatibility ([ffb6464](https://github.com/gee-community/qgis-earthengine-plugin/commit/ffb6464d6251aec05162428a370b81445a6ba096))

## [0.1.5](https://github.com/gee-community/qgis-earthengine-plugin/compare/v0.1.4...v0.1.5) (2025-11-13)


### Bug Fixes

* update bytes-per-pixel estimation to match EE Pixel accounting ([#415](https://github.com/gee-community/qgis-earthengine-plugin/issues/415)) ([3f1ace7](https://github.com/gee-community/qgis-earthengine-plugin/commit/3f1ace7762aa30d03849a7384e4c78275aa78a07))

## [0.1.4](https://github.com/gee-community/qgis-earthengine-plugin/compare/v0.1.3...v0.1.4) (2025-09-12)


### Bug Fixes

* dereferencing error on windows ([#408](https://github.com/gee-community/qgis-earthengine-plugin/issues/408)) ([e52a2f1](https://github.com/gee-community/qgis-earthengine-plugin/commit/e52a2f15d082a4fb096dbc05be2cf3c14719a9d0))
* remove query parameters to url that break xyz tile url ([#365](https://github.com/gee-community/qgis-earthengine-plugin/issues/365)) ([40ad9bc](https://github.com/gee-community/qgis-earthengine-plugin/commit/40ad9bc21bbe5d637ca2093a5c1e70d4326f0b14))

## [0.1.3](https://github.com/gee-community/qgis-earthengine-plugin/compare/v0.1.2...v0.1.3) (2025-08-24)


### Features

* add clip image by extent ([#387](https://github.com/gee-community/qgis-earthengine-plugin/issues/387)) ([1679d60](https://github.com/gee-community/qgis-earthengine-plugin/commit/1679d60fca2ed2bf414f19115f861c827bbb56df))


### Bug Fixes

* add handling of layer references from processing models ([#386](https://github.com/gee-community/qgis-earthengine-plugin/issues/386)) ([69cdfa9](https://github.com/gee-community/qgis-earthengine-plugin/commit/69cdfa9946b6bcd1487ccdcff46f46f1080bf453))
* robust extent and CRS handling in AddImageCollection ([#399](https://github.com/gee-community/qgis-earthengine-plugin/issues/399)) ([f098797](https://github.com/gee-community/qgis-earthengine-plugin/commit/f098797ca00d95c2cb32f905421201dede0a9eb8))

## [0.1.2](https://github.com/gee-community/qgis-earthengine-plugin/compare/v0.1.1...v0.1.2) (2025-08-15)


### Features

* refine async runs of algorithms ([#378](https://github.com/gee-community/qgis-earthengine-plugin/issues/378)) ([2191cd6](https://github.com/gee-community/qgis-earthengine-plugin/commit/2191cd66b42e01ecf3a762d9930ba92d08d03a2d))

## [0.1.1](https://github.com/gee-community/qgis-earthengine-plugin/compare/v0.1.0...v0.1.1) (2025-08-14)


### Features

* add band selection ([#374](https://github.com/gee-community/qgis-earthengine-plugin/issues/374)) ([df2ba45](https://github.com/gee-community/qgis-earthengine-plugin/commit/df2ba45475ec6080eae5bd11473a1ca804c71b14))
* implement async runs, unified progress, and cancellation of tasks ([#376](https://github.com/gee-community/qgis-earthengine-plugin/issues/376)) ([fbf5bbd](https://github.com/gee-community/qgis-earthengine-plugin/commit/fbf5bbdd34ec501d103b971d343c65f66ec1173a))


### Bug Fixes

* export geotiff bugs ([#369](https://github.com/gee-community/qgis-earthengine-plugin/issues/369)) ([28b6105](https://github.com/gee-community/qgis-earthengine-plugin/commit/28b61052075dcb8b1e1bcf9d8175cd195e734dec))

## [0.1.0](https://github.com/gee-community/qgis-earthengine-plugin/compare/v0.0.9...v0.1.0) (2025-07-30)

### Important Notes

* The `earthengine-api` dependency was updated, which changes the required authentication scopes.
  Users must reauthenticate using the **Sign-in** tool from the plugin toolbar to generate a new token.

### Features

* Add support for date range handling in processing algorithms ([#356](https://github.com/gee-community/qgis-earthengine-plugin/pull/356))
* Fix zoom to the extent of added layers ([#355](https://github.com/gee-community/qgis-earthengine-plugin/pull/355)
* Create separate launch commands for debugger vs. testing ([#353](https://github.com/gee-community/qgis-earthengine-plugin/pull/353))
* Update earthengineapi version, remove PyQt5 dependency, pin pyOpenSSL ([#352](update earthengineapi version, demove PyQt5 dependency, pin pyOpenSSL))

### CI/CD

* Make composite job for building extlibs and update CI python and paths ([#349](https://github.com/gee-community/qgis-earthengine-plugin/pull/349))


### Maintenance

* Update version number to 0.1.0 and regenerate manifest and changelog

## [0.0.9](https://github.com/gee-community/qgis-earthengine-plugin/compare/0.0.8...v0.0.9) (2025-07-09)


### Bug Fixes

* clean extra dependencies folder ([6ab50e0](https://github.com/gee-community/qgis-earthengine-plugin/commit/6ab50e08e44b7e6bdcb893760c3d1e5768399cf9))
* qgis plugin ci ([#335](https://github.com/gee-community/qgis-earthengine-plugin/issues/335)) ([6ab50e0](https://github.com/gee-community/qgis-earthengine-plugin/commit/6ab50e08e44b7e6bdcb893760c3d1e5768399cf9))
* reset release please version and set experimental to false ([6ab50e0](https://github.com/gee-community/qgis-earthengine-plugin/commit/6ab50e08e44b7e6bdcb893760c3d1e5768399cf9))
* update tag extration ([6ab50e0](https://github.com/gee-community/qgis-earthengine-plugin/commit/6ab50e08e44b7e6bdcb893760c3d1e5768399cf9))
* update token release please ([6ab50e0](https://github.com/gee-community/qgis-earthengine-plugin/commit/6ab50e08e44b7e6bdcb893760c3d1e5768399cf9))
* version number ([31c436b](https://github.com/gee-community/qgis-earthengine-plugin/commit/31c436b9d219ecbd3c368b9e237f9e83b0d36cf0))
* version number ([6ab50e0](https://github.com/gee-community/qgis-earthengine-plugin/commit/6ab50e08e44b7e6bdcb893760c3d1e5768399cf9))

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
