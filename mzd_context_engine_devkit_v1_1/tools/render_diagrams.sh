#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
for f in "$ROOT"/diagrams/*.dot; do
  base="${f%.dot}"
  dot -Tsvg "$f" -o "${base}.svg"
  dot -Tpng -Gdpi=160 "$f" -o "${base}.png"
  echo "rendered $(basename "$base")"
done
