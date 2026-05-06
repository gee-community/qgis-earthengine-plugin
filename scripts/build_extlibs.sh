#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXTLIBS_DIR="$ROOT_DIR/ee_plugin/extlibs"

if [[ -n "${EXTLIBS_PYTHON:-}" ]]; then
  PYTHON_BIN="$EXTLIBS_PYTHON"
elif command -v python3.12 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3.12)"
elif [[ -x "/Applications/QGIS.app/Contents/MacOS/python3.12" ]]; then
  PYTHON_BIN="/Applications/QGIS.app/Contents/MacOS/python3.12"
else
  PYTHON_BIN="$(command -v python3)"
fi

rm -rf "$EXTLIBS_DIR"
mkdir -p "$EXTLIBS_DIR"

env -u PYTHONHOME -u PYTHONPATH "$PYTHON_BIN" -m pip install --no-compile -r "$ROOT_DIR/requirements.txt" -t "$EXTLIBS_DIR"

# Keep the vendored bundle to runtime-only dependencies used by the plugin.
# Newer Earth Engine / google-auth releases require cryptography at runtime,
# so we only prune optional Cloud Storage and CLI helpers here.
rm -rf "$EXTLIBS_DIR/bin"
rm -rf "$EXTLIBS_DIR/ee/cli"
rm -rf "$EXTLIBS_DIR/google/cloud/storage"
rm -rf "$EXTLIBS_DIR/google_crc32c"
rm -rf "$EXTLIBS_DIR"/google_cloud_storage-*.dist-info
rm -rf "$EXTLIBS_DIR"/google_crc32c-*.dist-info
rm -rf "$EXTLIBS_DIR"/google_resumable_media-*.dist-info

# Tests are not needed in the packaged plugin and add scan noise.
find "$EXTLIBS_DIR" -type d \( -name tests -o -name testing \) -prune -exec rm -rf {} +
find "$EXTLIBS_DIR" -type d -name __pycache__ -exec rm -rf {} +
