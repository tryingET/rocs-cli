---
summary: "Normative cross-field, ordering, digest-preimage, and byte-accounting invariants for Semantic Discovery Protocol v0."
read_when:
  - "Implementing or independently verifying semantic-discovery-v0 schemas."
  - "Reviewing Python/TypeScript byte-identical protocol closure."
type: "specification"
status: "accepted"
---

# Semantic Discovery Protocol v0 — Normative Invariants

The sibling [`protocol.schema.json`](protocol.schema.json) owns structural validation. This document owns constraints not expressible portably in JSON Schema Draft 2020-12. Both are accepted normative development contracts under decision `52`; production adoption remains gated by decision `53`.

## Canonical strings and byte limits

- JSON Schema `minLength`/`maxLength` constraints count Unicode code points.
- Every RFC byte limit is additionally enforced over UTF-8 bytes and is authoritative when stricter.
- `name` is exactly ASCII regex `[A-Za-z0-9_-]+`.
- `ontId` is exactly ASCII regex `[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)+`.
- `token` is exactly the output of RFC normalization/tokenization: NFKC, Unicode casefold under Unicode 15.0.0, then one maximal run of `L*|N*` code points. A verifier recomputes this predicate; schema pattern alone is not sufficient.
- `python_version` is exactly `platform.python_version()` and must match `3.12.<decimal patch>`.

## Request and error hashing

- A syntactically valid I-JSON object with no duplicate keys is JCS-canonicalized and hashed with domain `rocs.caller-request.v0` before semantic schema validation.
- Therefore unknown fields, unsupported schema/algorithm/identity, wrong scalar types, and out-of-range integers still receive `caller_request_digest` when the parsed value is one I-JSON object.
- `caller_request_digest` is `null` only when UTF-8 decoding, JSON parsing, duplicate-key rejection, I-JSON validation, or top-level-object validation fails before JCS canonicalization.
- The nullable error field is the sole exception to the protocol's non-nullability rule.
- Error `message` is fixed safe adapter text, 1–4096 UTF-8 bytes, and is never included in identity or authority decisions.

## Digest-omitted pseudotypes

The following pseudotypes are hashed using the RFC domain and JCS bytes:

```text
ToolIdentityPreimage = ToolIdentity minus digest
CorpusSnapshotPreimage = CorpusSnapshot minus corpus_snapshot_digest
EffectiveExecutionPreimage = EffectiveExecution minus effective_execution_digest
DiscoveryResultPreimage = DiscoveryResult minus result_digest
PackResultPreimage = PackResult minus pack_digest
```

No omitted digest key is present with `null`; it is absent.

Prepared-runtime `manifest_digest` is computed by the Pi adapter over its separately closed staged-runtime manifest. `tool_identity.digest` binds that opaque manifest digest plus kind, canonical Python version, and Unicode data under `rocs.tool-identity.v0`.

## Snapshot relationships and order

- `layer_order` is unique across `roots`.
- `root_id` and `layer` are independently unique across `roots`.
- `roots` sort by `(layer_order, root_id UTF-8 bytes)`.
- Every `kind=ref` root has exactly one `resolved_refs` item with equal `layer` and `layer_order`; path roots have none.
- `resolved_refs` sort by `(layer_order, layer UTF-8 bytes, locator UTF-8 bytes)`.
- Snapshot entries have unique `(layer, logical_path)` and unique semantic IDs after parsing.
- Entries sort by `(layer_order, logical_path UTF-8 bytes, kind)`.
- The corpus snapshot digest is over the schema-valid snapshot object with its digest omitted.

## Evidence and scoring

- “Contains token” means membership in the normalized field token set, never substring containment.
- Token evidence uses `query_term=<one normalized query token>`.
- Phrase evidence uses `query_term=<complete normalized query string>`, which may contain spaces.
- Valid field/rule pairs are enforced by the schema's four evidence variants.
- The scoring accumulator uses signed arbitrary-precision integer arithmetic internally: add all positive token and phrase weights, subtract anti-token and anti-phrase weights, then clamp once to `0..4294967295`.
- Evidence generation is deterministic before budget enforcement. If one candidate would require more than 256 unique evidence items, invocation fails with `resource_exhausted`; evidence is never truncated.
- Evidence order is field family `id,label,synonym,description,relation,example,anti_example`, then rule `phrase_exact,token_exact,anti_phrase,anti_token`, then original normalized query-term order. Phrase terms use query position 0; token terms use first-occurrence query-token position. UTF-8 bytes break only impossible duplicate-position ties.
- `matched_query_tokens` contains each positive-matched normalized query token exactly once in original query-token order. Every positive token-evidence term is present in that array; negative-only terms are not.

## Candidate and result relationships

- Candidate identity `(ont_id,kind)` is unique.
- Candidate order is score descending, then `ont_id` UTF-8 bytes ascending, then kind `concept` before `relation`.
- Ranks are contiguous `1..len(candidates)` and equal array position.
- `len(candidates) <= effective_limits.candidates`.
- Candidates are exactly the first top-K eligible candidates under the normative order; no eligible higher-ranked candidate may be omitted.
- `truncated=true` iff the full eligible set is larger than the emitted candidate array.
- `no_candidates` requires zero emitted and zero eligible candidates.
- Every other retrieval state requires at least one emitted candidate and follows the RFC classification over the full eligible set before top-K.
- The normative result example must include all eight effective limits; `{}` is never valid.
- Result byte accounting is UTF-8 length of the final JCS object after inserting the 71-byte ASCII digest string (`sha256:` is 7 bytes plus 64 hex bytes).

## Pack relationships and order

- `rel_types` is duplicate-free and sorted by UTF-8 bytes.
- Documents have unique `(ont_id,kind)` and unique logical paths.
- The requested root document is always first; its ID equals `root_id` and digest equals `root_document_digest`.
- Remaining concept documents sort by ontology-ID UTF-8 bytes; relation documents follow, also sorted by ID bytes.
- `max_docs` counts every emitted document including root.
- `max_bytes` is the sum of UTF-8 byte lengths of every emitted `text` field before JSON escaping; the root must fit or the operation fails.
- Pack digest is JCS of the complete schema-valid pack result with `pack_digest` omitted, not a concatenation of external bytes.

## Pi structural projection

Pi renders each ROCS evidence object as the canonical string:

```text
<field>.<rule>
```

It sorts/deduplicates those strings by UTF-8 bytes for prompt display only. The full evidence objects remain in the validated machine result and control its digest. Labels are neither rendered nor validated as candidate fields in automatic prompt blocks.

## Required differential fixtures

Independent Python and TypeScript validators must agree on:

- every valid fixture;
- every invalid fixture and expected failing invariant or portable validator tuple `(instancePath, keyword)`; validator-specific `schemaPath` values are non-normative;
- JCS bytes and every digest preimage;
- result and pack omission behavior;
- error nullability;
- evidence projection;
- ordering and byte-limit boundary cases.
