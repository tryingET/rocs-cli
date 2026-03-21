#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT"
exec uv run python "$ROOT/scripts/run-fleet-audit-nightly.py" "$@"
