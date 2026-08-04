---
summary: "ROCS implementation boundary for Decision 110 ontology-markdown-v1 admission and schema-3 materialization receipts."
read_when:
  - "When enabling or changing ontology-markdown-v1 in a ROCS layer."
  - "When producing or verifying a self-contained ROCS materialization."
type: "reference"
---

# Ontology Markdown v1 implementation boundary

This is the `rocs-cli` implementation reference for accepted Decision 110. The
semantic owner remains `core/ontology-kernel`; this package evaluates only exact
source-contract, schema, and reference conformance. Nothing here establishes
semantic correctness, package publication, consumer adoption, activation,
currentness, or AK lifecycle state.

## Selector and compatibility

A layer opts in through the manifest adjacent to its source root:

```yaml
rocs:
  source_contract: ontology-markdown-v1
```

Resolution records the selector on each `LayerSpec`. Mixed views dispatch each
layer independently, then run resolved-corpus identity and reference checks.
Absent selectors retain the pre-v1 parser and recursive membership behavior.
Unknown or mistyped selectors fail as configuration errors rather than silently
falling back.

`src/rocs_cli/source_contract.py` is the sole v1 parser/dispatcher. The ordinary
model loader and immutable two-pass semantic snapshot both call it. V1 parsed
indexes are not reused from the legacy cache; exact current bytes are re-admitted
for each operation.

## Closed admission

V1 enforces the accepted profile:

- at most 1 MiB, strict UTF-8, no BOM;
- exact opening `---\n` and first later `\n---\n` closing delimiter;
- one safe YAML document with string mapping keys, depth at most 32, and at most
  10,000 mapping-key plus sequence-item entries;
- no duplicate keys, anchors, aliases, merges, explicit tags, shared/recursive
  nodes, additional document markers, or implicit substitutes for required field
  types;
- exact top-level and per-kind fields, lifecycle shapes, concept-only
  `system4d.fog`, empty-only `lint_ignore`, and relation presentation fields;
- normalized direct-child concept/relation paths, ID/path/type agreement, unique
  IDs and relation labels, same-kind replacement references, reciprocal inverses,
  and resolved relation-label/concept edges;
- no `<...>` placeholder token anywhere in an admitted v1 document.

Within `reference/concepts/` and `reference/relations/`, only direct regular
`*.md` files are definitions. Exact `README.md` is optional narrative and
excluded. Subdirectories, symlinks, special entries, and other regular files fail
closed.

Within one document, error precedence is resource, envelope, YAML, schema,
identity/path/uniqueness, lifecycle/reference, then placeholder. Across a corpus,
documents are admitted in deterministic logical-path order; this contract makes
no corpus-wide precedence claim across errors in different documents.
Semantic-discovery caller limits may be lower than the grammar maxima;
exhausting those limits returns `resource_exhausted` and does not reclassify the
source as valid or invalid.

## Interpreting operations

The shared dispatch path covers:

- `validate`, `build`, `summary`, `lint`, `diff`, `graph`, `check-inverses`, and
  `normalize`;
- unbound and snapshot-bound `pack`;
- `discover` and `route` immutable corpus capture;
- source reads in `transaction.prepare`, `transaction.simulate`,
  `transaction.apply`, `transaction.verify`, and `transaction.rollback`.

`rules` is registry-only. The current `explain` command describes a registry rule
without opening a document; if it later opens source, it must use the dispatcher.
`context.create` is intentionally outside admission: it stores caller-selected
UTF-8 bytes under its raw-custody capsule contract. A downstream transaction
re-admits the live selected layer before interpreting those bytes.

## Conformance claim ceiling

On supported open JSON/receipt surfaces, complete successful v1 operations may
include `rocs-source-contract-conformance.v1`. It names the exact operation,
uses the fixed scope `source-contract/schema/reference`, and binds a digest over
selected layer descriptors plus every admitted raw document digest.

The helper returns no claim for raw context capture, failed/partial operations,
or resource exhaustion. Closed semantic-discovery and routing protocol shapes
remain unchanged; their successful execution implies their existing bounded
admission path but gains no extra generic verdict field.

## Schema-3 materialization receipt

`rocs vendor` writes one exact local materialization receipt:

```json
{
  "schema_version": 3,
  "artifact": "rocs-cli-self-contained",
  "upstream_project": "ai-society/core/rocs-cli",
  "upstream_version": "<version>",
  "source_commit": "<40 lowercase Git SHA-1 hex>",
  "uv_lock_sha256": "<64 lowercase hex>",
  "files": {"<safe relative path>": "<64 lowercase hex>"},
  "bundle_manifest_digest": "sha256:<64 lowercase hex>"
}
```

`files` is the complete set of regular bundle files except the receipt itself.
Missing, extra, unsafe, symlink, and special paths reject. The lock digest must
equal bundled `uv.lock`. `bundle_manifest_digest` is plain SHA-256 over RFC 8785
JCS bytes of the exact receipt object with that digest field omitted.

Generation obtains `source_commit` from the repository's current Git SHA-1
commit, or inherits it only after exact schema-3 verification succeeds for the
complete source bundle. A non-Git installation without that provenance cannot
mint a schema-3 receipt. Installed legacy wheels retain a schema-2 bootstrap
fallback rather than inventing a Git identity; source checkout and verified
schema-3 re-vendoring paths emit schema 3. The receipt identifies one bundle; it
does not claim reproducibility across builders. Schema 1 and 2 remain verifier
compatibility inputs, and schema 2 remains the bounded installed-wheel fallback.

## Validation

Run from the package root:

```bash
uv run --frozen python -m unittest discover -s tests -p 'test_*.py' -q
./scripts/ci/full.sh
```

Focused adversarial and compatibility coverage is in
`tests/test_source_contract_v1.py`. Package release/version/lock mutation is a
separate owner task and is not part of this implementation boundary.
