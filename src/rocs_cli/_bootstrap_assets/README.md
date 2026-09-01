---
summary: "Runtime-local documentation seed for self-contained ROCS consumer artifacts."
read_when:
  - "Inspecting the files embedded into a bootstrapped ROCS consumer runtime."
type: "reference"
---

# ROCS self-contained consumer runtime

This file is packaged as an immutable bootstrap seed. `rocs bootstrap` publishes a
hash-complete consumer artifact under `tools/rocs-cli/` and records every runtime
file in `VENDORED_HASHES.json`.

Generated wrappers use isolated system Python (`python3 -I -S -B`) and import the
captured `rocs_cli.__main__` directly. The artifact does not discover a source
checkout, use ambient `PYTHONPATH`, require `uv`, fetch dependencies, or contact a
remote service.

Both generated wrappers embed the expected digest of `VENDORED_HASHES.json`. Its stdlib-only launcher descriptor-captures every listed
regular, singly linked file without following final symlinks and writes only the
verified bytes to an anonymous ZIP memfd. After the archive is reread and sealed
against writes/growth/shrinkage, Python and resource imports resolve through that
descriptor; ABI-compatible native extensions use separately sealed and rehashed
memfds. ROCS commands fork without exec from the custody process, so no consumer
or temporary filesystem path is reopened and replacements after capture cannot
redirect imports. `scripts/rocs.sh` forwards the caller's exact ROCS argv and
stdin; `scripts/ci/full.sh` separately retains its fixed cleanup, validate, and
build sequence. Both preserve an optional `ROCS_OUTPUT_ROOT` binding. Cleanup of
that marked external root removes only the closed ROCS artifact registry and exact
orphan temporaries, retains the stable authority lock and marker, and fails on
unknown or racing entries.
