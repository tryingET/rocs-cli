#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: scripts/vendor-to.sh <target> [--version X.Y.Z] [--dry-run]"
  echo
  echo "Copies rocs-cli source-of-truth files into <target> and writes"
  echo "VENDORED_HASHES.json for downstream integrity checks."
}

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_PROJECT="ai-society/core/rocs-cli"

TARGET=""
VERSION_OVERRIDE=""
DRY_RUN=0

while (($# > 0)); do
  case "$1" in
    --version)
      if (($# < 2)); then
        echo "error: --version requires a value" >&2
        usage >&2
        exit 2
      fi
      VERSION_OVERRIDE="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [[ -n "$TARGET" ]]; then
        echo "error: unexpected positional argument: $1" >&2
        usage >&2
        exit 2
      fi
      TARGET="$1"
      shift
      ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  echo "error: missing required <target>" >&2
  usage >&2
  exit 2
fi

python3 - "$ROOT" "$TARGET" "$UPSTREAM_PROJECT" "$VERSION_OVERRIDE" "$DRY_RUN" <<'PY'
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path


repo_root = Path(sys.argv[1]).resolve()
target_raw = Path(sys.argv[2]).expanduser()
upstream_project = sys.argv[3]
version_override = sys.argv[4].strip()
dry_run = sys.argv[5] == "1"

if target_raw.is_absolute():
    target = target_raw.resolve()
else:
    target = (Path.cwd() / target_raw).resolve()

sys.path.insert(0, str(repo_root / "src"))
from rocs_cli.vendored import compute_expected_hashes, validate_vendor_source_layout, validate_vendor_target


def read_version(path: Path) -> str:
    m = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"\s*$', path.read_text("utf-8"))
    if not m:
        raise SystemExit(f"version not found in {path}")
    return m.group(1)


def remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


try:
    pyproject, readme, src_pkg = validate_vendor_source_layout(repo_root)
    validate_vendor_target(repo_root=repo_root, target=target)
except ValueError as e:
    raise SystemExit(str(e)) from e

upstream_version = version_override or read_version(pyproject)
hashes_path = target / "VENDORED_HASHES.json"

if dry_run:
    print(f"[dry-run] target: {target}")
    print(f"[dry-run] upstream_project: {upstream_project}")
    print(f"[dry-run] upstream_version: {upstream_version}")
    print("[dry-run] would sync: pyproject.toml, README.md, src/rocs_cli")
    print(f"[dry-run] would write: {hashes_path}")
    raise SystemExit(0)

target.mkdir(parents=True, exist_ok=True)

for cruft in ("build", "dist"):
    remove_path(target / cruft)

src_dir = target / "src"
src_dir.mkdir(parents=True, exist_ok=True)

for egg in src_dir.glob("*.egg-info"):
    remove_path(egg)

remove_path(src_dir / "rocs_cli")
shutil.copytree(src_pkg, src_dir / "rocs_cli")
shutil.copyfile(pyproject, target / "pyproject.toml")
shutil.copyfile(readme, target / "README.md")

payload = {
    "schema_version": 1,
    "upstream_project": upstream_project,
    "upstream_version": upstream_version,
    "files": compute_expected_hashes(target),
}

hashes_path.write_text(json.dumps(payload, indent=2) + "\n", "utf-8")

print(f"vendored: {target}")
print(f"upstream_project: {upstream_project}")
print(f"upstream_version: {upstream_version}")
print(f"wrote: {hashes_path}")
PY
