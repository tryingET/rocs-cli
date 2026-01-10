#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VHS_BIN="${VHS_BIN:-vhs}"
OUT_DIR="${OUT_DIR:-artifacts/vhs}"

mkdir -p "$OUT_DIR"

if ! command -v "$VHS_BIN" >/dev/null 2>&1; then
  echo "missing vhs binary: $VHS_BIN"
  echo "install VHS (plus ttyd + ffmpeg), then re-run:"
  echo "  core/rocs-cli/scripts/vhs-run.sh"
  exit 2
fi

shopt -s nullglob
for tape in tapes/*.tape; do
  echo "vhs: $tape"
  "$VHS_BIN" "$tape"
done

echo "wrote: $OUT_DIR"
