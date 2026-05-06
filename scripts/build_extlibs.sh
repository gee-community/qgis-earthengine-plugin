#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXTLIBS_DIR="$ROOT_DIR/ee_plugin/extlibs"

rm -rf "$EXTLIBS_DIR"
mkdir -p "$EXTLIBS_DIR"

pip install --no-compile -r "$ROOT_DIR/requirements.txt" -t "$EXTLIBS_DIR"

# Keep the vendored bundle to runtime-only dependencies used by the plugin.
# Earth Engine's CLI / Cloud Storage helper stack pulls in crypto packages
# that QGIS plugin repository scanning now blocks, but the plugin imports
# only the EE client library and requests stack.
rm -rf "$EXTLIBS_DIR/bin"
rm -rf "$EXTLIBS_DIR/ee/cli"
rm -rf "$EXTLIBS_DIR/google/cloud/storage"
rm -rf "$EXTLIBS_DIR/google_crc32c"
rm -rf "$EXTLIBS_DIR/cryptography"
rm -rf "$EXTLIBS_DIR/cffi"
rm -rf "$EXTLIBS_DIR/pycparser"
rm -rf "$EXTLIBS_DIR"/google_cloud_storage-*.dist-info
rm -rf "$EXTLIBS_DIR"/google_crc32c-*.dist-info
rm -rf "$EXTLIBS_DIR"/google_resumable_media-*.dist-info
rm -rf "$EXTLIBS_DIR"/cryptography-*.dist-info
rm -rf "$EXTLIBS_DIR"/cffi-*.dist-info
rm -rf "$EXTLIBS_DIR"/pycparser-*.dist-info

# Tests are not needed in the packaged plugin and add scan noise.
find "$EXTLIBS_DIR" -type d \( -name tests -o -name testing \) -prune -exec rm -rf {} +
find "$EXTLIBS_DIR" -type f \( -name '*.so' -o -name '*.pyd' -o -name '*.dylib' \) -delete
find "$EXTLIBS_DIR" -type d -name __pycache__ -exec rm -rf {} +
