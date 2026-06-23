#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PARENT="$(dirname "$ROOT")"
NAME="$(basename "$ROOT")"

python "$ROOT/tools/generate_manifest.py"
python "$ROOT/tools/validate_package.py"

rm -rf "$ROOT/.pytest_cache" "$ROOT/starter/backend/.pytest_cache"
find "$ROOT" -type d -name __pycache__ -prune -exec rm -rf {} +
rm -f "$PARENT/${NAME}.zip"
(
  cd "$PARENT"
  zip -qr "${NAME}.zip" "$NAME" \
    -x '*/__pycache__/*' '*/.pytest_cache/*' '*/.DS_Store'
)
sha256sum "$PARENT/${NAME}.zip" > "$PARENT/${NAME}.zip.sha256"
echo "created $PARENT/${NAME}.zip"
