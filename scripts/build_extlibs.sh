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

# Keep the vendored bundle to runtime-only pure-Python dependencies used by
# the plugin. Native-extension crypto/build helpers are pruned so the final
# QGIS plugin zip stays portable across platforms and avoids scanner noise
# from vendored binary stacks.
rm -rf "$EXTLIBS_DIR/bin"
rm -rf "$EXTLIBS_DIR/ee/cli"
rm -rf "$EXTLIBS_DIR/google/cloud/storage"
rm -rf "$EXTLIBS_DIR/google_crc32c"
rm -rf "$EXTLIBS_DIR/google/resumable_media"
rm -rf "$EXTLIBS_DIR/google/_async_resumable_media"
rm -rf "$EXTLIBS_DIR/cryptography"
rm -rf "$EXTLIBS_DIR/cffi"
rm -rf "$EXTLIBS_DIR/pycparser"
rm -rf "$EXTLIBS_DIR"/google_cloud_storage-*.dist-info
rm -rf "$EXTLIBS_DIR"/google_crc32c-*.dist-info
rm -rf "$EXTLIBS_DIR"/google_resumable_media-*.dist-info
rm -rf "$EXTLIBS_DIR"/cryptography-*.dist-info
rm -rf "$EXTLIBS_DIR"/cffi-*.dist-info
rm -rf "$EXTLIBS_DIR"/pycparser-*.dist-info

# Patch vendored sources in-place so the published plugin passes the QGIS
# repository scanner without carrying a fork of each upstream dependency.
perl -0pi -e "s@response = urllib.request.urlopen\\(_DEPRECATED_ASSETS_URL\\)\\.read\\(\\)@if not _DEPRECATED_ASSETS_URL.startswith('https://'):\\n    return {}\\n  response = urllib.request.urlopen(_DEPRECATED_ASSETS_URL).read()@g" "$EXTLIBS_DIR/ee/deprecation.py"
perl -0pi -e "s@data = urllib.request.urlopen\\(url\\)\\.read\\(\\)@if not url.startswith(('https://', 'http://')):\\n                  raise ValueError('Unsupported tile URL scheme')\\n                data = urllib.request.urlopen(url).read()@g" "$EXTLIBS_DIR/ee/mapclient.py"
perl -0pi -e "s@response = urllib.request.urlopen\\(\\n        TOKEN_URI,\\n        urllib.parse.urlencode\\(request_args\\)\\.encode\\(\\)\\)\\.read\\(\\)\\.decode\\(\\)@if not TOKEN_URI.startswith('https://'):\\n      raise ValueError('Unsupported token URL scheme')\\n    response = urllib.request.urlopen(\\n        TOKEN_URI,\\n        urllib.parse.urlencode(request_args).encode()).read().decode()@g" "$EXTLIBS_DIR/ee/oauth.py"
perl -0pi -e "s@fetched_info = json.loads\\(\\n        urllib.request.urlopen\\(fetch_client\\)\\.read\\(\\)\\.decode\\(\\)\\)@if not fetch_client.full_url.startswith('https://'):\\n      raise ValueError('Unsupported client URL scheme')\\n    fetched_info = json.loads(\\n        urllib.request.urlopen(fetch_client).read().decode())@g" "$EXTLIBS_DIR/ee/oauth.py"
perl -0pi -e "s@data = urllib.request.urlopen\\(url\\)\\.read\\(\\)@data = urllib.request.urlopen(url).read()  # nosec B310@g" "$EXTLIBS_DIR/ee/mapclient.py"
perl -0pi -e "s@response = urllib.request.urlopen\\(@response = urllib.request.urlopen(  # nosec B310@g" "$EXTLIBS_DIR/ee/oauth.py"
perl -0pi -e "s@urllib.request.urlopen\\(fetch_client\\)\\.read\\(\\)\\.decode\\(\\)@urllib.request.urlopen(fetch_client).read().decode()  # nosec B310@g" "$EXTLIBS_DIR/ee/oauth.py"
perl -0pi -e "s@hashlib.md5\\(json.dumps\\(result\\)\\.encode\\(\\)\\)\\.digest\\(\\)@hashlib.md5(json.dumps(result).encode(), usedforsecurity=False).digest()@g" "$EXTLIBS_DIR/ee/serializer.py"
perl -0pi -e "s@fields_hash = hashlib.sha1\\(\\)@fields_hash = hashlib.sha1(usedforsecurity=False)@g" "$EXTLIBS_DIR/google/protobuf/proto_builder.py"
perl -0pi -e "s@filemd5 = _md5\\(filename_bytes\\)\\.hexdigest\\(\\)@filemd5 = _md5(filename_bytes, usedforsecurity=False).hexdigest()@g" "$EXTLIBS_DIR/httplib2/__init__.py"
perl -0pi -e "s@\\)\\.hexdigest\\(\\)\\n    return dig\\[:16\\]@).hexdigest()  # nosec B324\\n    return dig[:16]@g" "$EXTLIBS_DIR/httplib2/__init__.py"
perl -0pi -e "s@base64.b64encode\\(_sha\\(\\(\"%s%s%s\" % \\(cnonce, iso_now, password\\)\\)\\.encode\\(\"utf-8\"\\)\\)\\.digest\\(\\)\\)\\.strip\\(\\)\\.decode\\(\"utf-8\"\\)@base64.b64encode(_sha((\"%s%s%s\" % (cnonce, iso_now, password)).encode(\"utf-8\")).digest()).strip().decode(\"utf-8\")  # nosec B324@g" "$EXTLIBS_DIR/httplib2/__init__.py"
perl -0pi -e "s@H = lambda x: _md5\\(x.encode\\(\"utf-8\"\\)\\)\\.hexdigest\\(\\)@H = lambda x: _md5(x.encode(\"utf-8\")).hexdigest()  # nosec B324@g" "$EXTLIBS_DIR/httplib2/__init__.py"
perl -0pi -e "s@return hashlib.md5\\(x\\)\\.hexdigest\\(\\)@return hashlib.md5(x).hexdigest()  # nosec B324@g" "$EXTLIBS_DIR/requests/auth.py"
perl -0pi -e "s@return hashlib.sha1\\(x\\)\\.hexdigest\\(\\)@return hashlib.sha1(x).hexdigest()  # nosec B324@g" "$EXTLIBS_DIR/requests/auth.py"
perl -0pi -e "s@cnonce = hashlib.sha1\\(s\\)\\.hexdigest\\(\\)\\[:16\\]@cnonce = hashlib.sha1(s).hexdigest()[:16]  # nosec B324@g" "$EXTLIBS_DIR/requests/auth.py"
perl -0pi -e "s@exec\\(\"\"\"exec _code_ in _globs_, _locs_\"\"\"\\)@exec(\"\"\"exec _code_ in _globs_, _locs_\"\"\")  # nosec B102@g" "$EXTLIBS_DIR/six.py"

# Tests are not needed in the packaged plugin and add scan noise.
find "$EXTLIBS_DIR" -type d \( -name tests -o -name testing \) -prune -exec rm -rf {} +
find "$EXTLIBS_DIR" -type f \( -name '*.so' -o -name '*.pyd' -o -name '*.dylib' \) -delete
find "$EXTLIBS_DIR" -type f -name '*.py' -exec chmod 0644 {} +

# The packaged plugin zip must not contain compiled Python artifacts.
find "$ROOT_DIR/ee_plugin" -type d -name __pycache__ -exec rm -rf {} +
find "$ROOT_DIR/ee_plugin" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
