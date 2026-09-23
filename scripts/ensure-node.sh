#!/usr/bin/env bash
# Provision the exact Node runtime pinned in scripts/tool_versions.json and print its
# install root. The gate uses it instead of the system Node, so a package-manager
# upgrade cannot change which runtime the Decision 85 conformance evidence runs under.
# The official nodejs.org tarball is fetched once, verified against the release's
# SHASUMS256.txt, and cached under ${ROCS_NODE_CACHE:-${XDG_CACHE_HOME:-~/.cache}/rocs/node}.
set -euo pipefail

repo="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
version="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["node"])' "$repo/scripts/tool_versions.json")"
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "error: invalid node pin: $version" >&2; exit 2; }

case "$(uname -s)-$(uname -m)" in
  Linux-x86_64) platform="linux-x64" ;;
  Linux-aarch64) platform="linux-arm64" ;;
  Darwin-arm64) platform="darwin-arm64" ;;
  Darwin-x86_64) platform="darwin-x64" ;;
  *) echo "error: unsupported platform for pinned node: $(uname -s)-$(uname -m)" >&2; exit 2 ;;
esac

cache="${ROCS_NODE_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/rocs/node}"
name="node-v$version-$platform"
root="$cache/$name"
if [[ -x "$root/bin/node" && "$("$root/bin/node" --version)" == "v$version" ]]; then
  printf '%s\n' "$root"
  exit 0
fi

mkdir -p -- "$cache"
stage="$(mktemp -d "$cache/.$name.XXXXXX")"
trap 'rm -rf -- "$stage"' EXIT
base="https://nodejs.org/dist/v$version"
curl -fsSL -o "$stage/$name.tar.xz" "$base/$name.tar.xz"
curl -fsSL -o "$stage/SHASUMS256.txt" "$base/SHASUMS256.txt"
expected="$(awk -v f="$name.tar.xz" '$2 == f {print $1}' "$stage/SHASUMS256.txt")"
[[ -n "$expected" ]] || { echo "error: $name.tar.xz missing from SHASUMS256.txt" >&2; exit 1; }
if command -v sha256sum >/dev/null 2>&1; then sum=(sha256sum); else sum=(shasum -a 256); fi
actual="$("${sum[@]}" "$stage/$name.tar.xz" | cut -d' ' -f1)"
[[ "$actual" == "$expected" ]] || { echo "error: checksum mismatch for $name.tar.xz" >&2; exit 1; }
tar -xJf "$stage/$name.tar.xz" -C "$stage"
[[ "$("$stage/$name/bin/node" --version)" == "v$version" ]] || { echo "error: unpacked node is not v$version" >&2; exit 1; }
rm -rf -- "$root"
mv -- "$stage/$name" "$root"
printf '%s\n' "$root"
