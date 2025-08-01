# Changelog

All notable changes to this project will be documented in this file.

## [0.1.1](https://github.com/gee-community/qgis-earthengine-plugin/compare/v0.1.0...v0.1.1) (2025-08-01)


### Features

* AddImage, ImageCollection, FeatureCollection, and Export tools ([#273](https://github.com/gee-community/qgis-earthengine-plugin/issues/273)) ([a07dc9b](https://github.com/gee-community/qgis-earthengine-plugin/commit/a07dc9bd3778650c39ff3ef2c2af6e579e884647))


### Bug Fixes

* 117, implement identify tool for v3.22 ([2be5068](https://github.com/gee-community/qgis-earthengine-plugin/commit/2be5068db3f5b5ead0ee9262e1ad96c6d8d7c4d2))
* 117, implement identify tool for v3.22 ([065fbe5](https://github.com/gee-community/qgis-earthengine-plugin/commit/065fbe5ef486c711fa18e7b1c707fef5b7806346))
* add date range handling ([#356](https://github.com/gee-community/qgis-earthengine-plugin/issues/356)) ([347447e](https://github.com/gee-community/qgis-earthengine-plugin/commit/347447ec7c34ab4928d576eb984938cfb307fc6f))
* clean extra dependencies folder ([6ab50e0](https://github.com/gee-community/qgis-earthengine-plugin/commit/6ab50e08e44b7e6bdcb893760c3d1e5768399cf9))
* create two separate launch commands for debugger vs. testing ([#353](https://github.com/gee-community/qgis-earthengine-plugin/issues/353)) ([a815a89](https://github.com/gee-community/qgis-earthengine-plugin/commit/a815a8997f14e25c2beaa0fd112c55dc5164ef7c))
* move depedency install to separate step ([#362](https://github.com/gee-community/qgis-earthengine-plugin/issues/362)) ([1d0e129](https://github.com/gee-community/qgis-earthengine-plugin/commit/1d0e1298fc689c96adef3a880328cb5ed2693f7c))
* qgis plugin ci ([#335](https://github.com/gee-community/qgis-earthengine-plugin/issues/335)) ([6ab50e0](https://github.com/gee-community/qgis-earthengine-plugin/commit/6ab50e08e44b7e6bdcb893760c3d1e5768399cf9))
* remove width and height from svg ([#337](https://github.com/gee-community/qgis-earthengine-plugin/issues/337)) ([308c5a6](https://github.com/gee-community/qgis-earthengine-plugin/commit/308c5a6a76e5ad3d667fe4c02e3cef396e905917))
* reset release please version and set experimental to false ([6ab50e0](https://github.com/gee-community/qgis-earthengine-plugin/commit/6ab50e08e44b7e6bdcb893760c3d1e5768399cf9))
* set layer extent from ee_object ([#355](https://github.com/gee-community/qgis-earthengine-plugin/issues/355)) ([a8fc178](https://github.com/gee-community/qgis-earthengine-plugin/commit/a8fc1786f8c45af1dd4a21e058d5557124fad92d))
* update tag extration ([6ab50e0](https://github.com/gee-community/qgis-earthengine-plugin/commit/6ab50e08e44b7e6bdcb893760c3d1e5768399cf9))
* update token release please ([6ab50e0](https://github.com/gee-community/qgis-earthengine-plugin/commit/6ab50e08e44b7e6bdcb893760c3d1e5768399cf9))
* version number ([31c436b](https://github.com/gee-community/qgis-earthengine-plugin/commit/31c436b9d219ecbd3c368b9e237f9e83b0d36cf0))
* version number ([6ab50e0](https://github.com/gee-community/qgis-earthengine-plugin/commit/6ab50e08e44b7e6bdcb893760c3d1e5768399cf9))

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
