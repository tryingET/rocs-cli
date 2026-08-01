---
summary: "Normative cross-field, digest, ordering, and state invariants for Semantic Router Protocol v0."
read_when:
  - "Implementing or independently verifying semantic-router-v0."
type: "protocol_invariants"
status: "proposed"
---
# Semantic Router Protocol v0 invariants

This document is normative with `protocol.schema.json`. Schema-valid objects that violate an invariant are invalid.

## Canonical JSON and digests

Route protocol inputs are strict UTF-8, duplicate-key-free, integer-only I-JSON. Floating-point and non-finite values, invalid Unicode scalar values, and integers outside the I-JSON safe range are forbidden.

Canonical bytes use RFC 8785 JCS.

Digest construction is:

```text
SHA-256(ASCII(domain-separator) || 0x00 || JCS(preimage))
```

| Kind | Domain separator | Preimage |
|---|---|---|
| Routing policy | `rocs.routing-policy.v0` | complete policy with `routing_policy_digest` omitted |
| Routing provenance | `rocs.routing-provenance.v0` | complete provenance manifest with `provenance_manifest_digest` omitted |
| Caller request | `rocs.route-caller-request.v0` | complete request |
| Effective execution | `rocs.route-effective-execution.v0` | complete effective execution with `effective_execution_digest` omitted |
| Route result | `rocs.route-result.v0` | complete result with `result_digest` omitted |

Existing discovery, corpus, document, tool, effective-execution, result, and pack digest domains and preimages are unchanged.

## Normalization and tokenization

Coordinates are exactly:

- Unicode data: `15.0.0`;
- normalization: `nfkc-casefold-ws-v0`;
- tokenization: `unicode-ln-sequence-v0`.

Normalization applies Unicode NFKC, full casefold, and whitespace collapse. Tokenization then emits the complete ordered sequence of maximal contiguous Unicode Letter or Number runs. Repeated tokens remain repeated. Token indices are zero-based half-open indices over this full sequence.

Discovery's deduplicating `lexical_tokens()` helper must not supply route witness positions.

A policy `token` alternative must already equal exactly one canonical token. A `phrase` alternative must already equal the single-space join of at least two canonical tokens. An alternative that changes under canonicalization is invalid. Alternatives with identical canonical token sequences in one group are duplicates even if raw spellings differ.

## Policy authority and development boundary

A policy authority object binds exact owner repository, 40-hex Git revision, repository-relative source path, source content digest, and owner review reference. `source_content_digest` is `sha256:` plus lowercase SHA-256 of the exact raw Git blob bytes resolved by `revision:path`; it is not the policy-file digest and has no recursive preimage. These coordinates establish provenance, not adoption by themselves.

Adopted use requires a currently published owner-local coordinate and publication receipt for the exact policy, provenance-manifest, corpus, and owner source digests. Owner withdrawal makes the coordinate immediately ineligible for new invocation and triggers the consumer owner's separately authorized deactivation/rollback gate. Withdrawal never satisfies publication eligibility. ROCS records and enforces supplied adopted-coordinate status but does not publish, withdraw, activate, or roll back. A local path and digest alone never establish semantic authority.

Development implementation may use only conspicuously synthetic policies. A synthetic fixture still carries exact repository/revision/path/digest coordinates but cannot claim real-domain authority. Any non-synthetic policy instance requires a separate ontology-owner task and review.

## Policy identity and ordering

All policy objects are closed. Unknown fields fail.

Input arrays must already be in canonical order; implementations reject rather than silently reorder:

- concepts: `ont_id` UTF-8 byte order;
- joint routes: `joint_route_id` UTF-8 byte order;
- clauses: `clause_id` UTF-8 byte order;
- groups: `group_id` UTF-8 byte order;
- alternatives: `token` before `phrase`, then canonical value UTF-8 bytes;
- joint-route `ont_ids`: ontology ID UTF-8 byte order.

Clause IDs are globally unique across domain, concept, and joint-route clauses. Group IDs are globally unique across all clauses. Policy, domain, clause, group, and joint-route IDs are non-empty ASCII identifiers no longer than 256 bytes. Joint-route ontology-ID sets are unique; duplicate sets are invalid.

Every concept policy ID and joint-route ontology ID identifies exactly one concept in the captured corpus. Relation IDs, duplicate IDs, and absent IDs make the policy invalid.

Required emptiness rules:

- domain `admit_any`: non-empty;
- domain `exclude_any`: present, possibly empty;
- concept `support_any`: non-empty;
- concept `exclude_any`: present, possibly empty;
- joint-route `support_any`: non-empty;
- joint-route `exclude_any`: present, possibly empty.

## Provenance manifest binding

The policy contains `provenance_manifest_digest`; the route request contains both expected policy and provenance digests. The exact manifest validates as `semantic-routing-provenance.v0` and its digest uses `rocs.routing-provenance.v0`.

Manifest policy identity and authority coordinates must exactly equal the policy's `policy_id`, owner repository, revision, path, and `source_content_digest`.

Each policy alternative has one stable coordinate:

```text
(clause_id, group_id, kind, canonical_value)
```

The provenance manifest contains exactly one record for every policy alternative coordinate and no extra record. Record ordering is clause ID, group ID, kind (`token` before `phrase`), then canonical value, all by UTF-8 bytes after kind. The record source blob digest is computed by the same raw-Git-blob rule as policy authority.

Policy, manifest, request, effective execution, and result provenance digests must all agree. Missing, duplicate, unbound, or mismatched records make the policy invalid.

## Pre-parse request envelope

Before JSON parsing, the CLI reads at most `262,145` bytes from stdin. A route request envelope larger than `262,144` bytes is `invalid_request`. A bounded duplicate-detecting parser enforces absolute pre-request maxima of depth `32` and collection items `20,000` before any request-supplied limit is trusted. Invalid UTF-8, duplicate keys, non-I-JSON numbers, excessive whitespace bytes, unknown structure, depth exhaustion, and item exhaustion fail safely without consulting request fields.

The same absolute pre-parse discipline applies independently to policy and provenance files, using the hard protocol maxima before their internal limits or identities are trusted.

## Resource accounting

All schema maxima apply simultaneously. In addition:

- total clauses counts domain, concept, and joint-route positive and exclusion clauses;
- total alternatives counts every alternative occurrence;
- normalized alternative bytes sum UTF-8 bytes of every canonical alternative occurrence;
- witnesses count every emitted group witness;
- evidence entries count every matched clause evidence object;
- matching work is `query_token_count × total_alternative_token_count` and must not exceed the request limit;
- collection items count every policy object and array member visited by the parser;
- parser depth is measured before semantic interpretation;
- result bytes are JCS bytes of the complete route result, including the nested discovery result.

Resource exhaustion is an error. It never becomes abstention.

## Filesystem capture

The CLI accepts an existing `--routing-policy-root` directory plus root-relative policy and provenance-manifest paths. Both files use the same anchored capture contract.

- Open and retain an `O_DIRECTORY|O_NOFOLLOW` root descriptor.
- Reject absolute paths, `..`, empty segments, NUL, and path components not representable as UTF-8.
- Open every intermediate component relative to the retained descriptor with `O_DIRECTORY|O_NOFOLLOW`.
- Open the final component with `O_RDONLY|O_NOFOLLOW`.
- Require a regular file.
- Read each file at most its hard protocol byte maximum plus one byte.
- Record device, inode, mode, size, mtime-ns, and content digest before parsing.
- Recheck the open descriptor and anchored path after execution.
- Any identity or content change is `snapshot_changed`.

Policy and corpus roots must be isolated. No network resolver exists. Ref resolution is disabled by default; any future ref mode requires a workspace root argument and strict mode under separate authorization.

The router schema registry is a fixed offline map. The canonical discovery schema ID `https://ai-society.local/rocs/semantic-discovery-v0/protocol.schema.json` resolves only to the protected checked-in discovery schema and its generated embedded copy. Unknown IDs and every network resolution attempt fail closed.

## Derived discovery request

For every valid route request, derive exactly one `semantic-discovery-request.v0`:

- copy `query` byte-for-byte;
- copy `identity_selector` structurally;
- copy `profile`;
- set `algorithm` to `rocs-lexical-v0`;
- copy `discovery_limits` as `limits`.

No ambient default or policy field influences this projection.

Execute unchanged discovery exactly once. The complete unchanged `semantic-discovery-result.v0`, including its `result_digest`, is nested in the route result.

The nested result must satisfy:

- caller-request digest equals the digest of the exact derived discovery request;
- corpus snapshot digest equals the route result corpus snapshot digest;
- tool identity equals the route tool identity;
- algorithm is the unchanged lexical algorithm;
- effective limits equal route-request discovery limits;
- effective-execution digest equals the route effective execution's nested digest field;
- all existing discovery schema, digest, and invariant checks pass.

There is no digest-only lexical reference and no derived score-zero discovery candidate.

Route effective execution and result both bind the exact provenance-manifest digest supplied by the request and validated against the policy.

## Clause matching and witnesses

A group matches when at least one alternative matches. A clause matches when every group matches. A `*_any` collection matches when at least one clause matches.

For each matched group emit exactly one canonical witness selected by:

1. lowest start-token index;
2. lowest end-token index;
3. `token` before `phrase` when spans are identical;
4. canonical alternative UTF-8 byte order.

Witness `end_token` is exclusive and greater than `start_token`. The witnessed query token sequence must exactly equal the alternative's canonical token sequence.

Within each evidence object witnesses are ordered by `group_id`. Evidence objects are ordered by:

1. scope order `domain`, `concept`, `joint_route`;
2. `ont_id` or empty string UTF-8 bytes;
3. `joint_route_id` or empty string UTF-8 bytes;
4. polarity order `support`, `exclusion`;
5. `clause_id` UTF-8 bytes.

Support and exclusion clause-ID arrays are UTF-8 sorted and duplicate-free. Supported, conflicted, and selected ontology-ID arrays are UTF-8 sorted and duplicate-free.

Evidence scope coordinates are closed:

- `domain`: `ont_id` and `joint_route_id` are null;
- `concept`: `ont_id` is a valid policy concept and `joint_route_id` is null;
- `joint_route`: `ont_id` is null and `joint_route_id` is a valid policy joint-route ID.

Every evidence clause belongs to the stated policy scope and polarity. Every witness group belongs to that clause. Every witness kind/value is an exact alternative in that group, and its span matches the query token sequence. The evidence array contains exactly one object for every matched positive and exclusion clause used to derive domain, concept, and evaluated joint-route state, with no omission, duplicate, or extra object. Admission clause arrays exactly equal matched domain evidence IDs. Supported/conflicted arrays exactly equal policy evaluation. A fabricated or misattributed evidence object invalidates the result.

## Admission matrix

Let `D+` be matched domain positive clauses and `D-` matched domain exclusions.

| Condition | Admission state | Reason |
|---|---|---|
| `D+` empty, `D-` empty | `abstained` | `no_policy_domain_support` |
| `D+` empty, `D-` non-empty | `abstained` | `explicit_domain_exclusion` |
| `D+` non-empty, `D-` non-empty | `abstained` | `domain_support_exclusion_conflict` |
| `D+` non-empty, `D-` empty | `admitted` | `domain_support` |

`no_policy_domain_support` means only that no admission clause matched under the exact policy, corpus, profile, and request coordinate. It is not a universal out-of-domain judgment.

When admission abstains, routing is `not_evaluated/admission_abstained`; every routing ID array is empty and `joint_route_id` is null.

## Concept state

For each concept:

- supported: at least one positive clause and no exclusion matches;
- conflicted: at least one positive clause and at least one exclusion matches;
- unsupported: no positive clause matches, regardless of exclusion-only evidence.

Let `S` be the exact set of supported concepts and `C` the exact set of conflicted concepts.

Any non-empty `C` yields routing `abstained/concept_support_exclusion_conflict`; selected IDs are empty. The result still records all supported and conflicted IDs and evidence.

## Routing matrix

Applied only after admitted domain state and empty `C`:

| Condition | Routing state | Reason | Selection |
|---|---|---|---|
| `S` empty | `abstained` | `no_concept_support` | empty |
| `|S| = 1` | `single` | `single_supported_concept` | exactly `S` |
| `|S| > 1`, no joint route has `ont_ids = S` | `ambiguous` | `multiple_supported_without_joint_route` | empty |
| `|S| > 1`, exact joint route positive does not match | `ambiguous` | `multiple_supported_without_joint_route` | empty |
| `|S| > 1`, exact joint positive and exclusion both match | `abstained` | `joint_route_exclusion` | empty |
| `|S| > 1`, exact joint positive matches and exclusion does not | `multi` | `explicit_joint_route` | exactly `S` |

Joint routes are not evaluated when `|S| <= 1`. Duplicate joint ontology-ID sets are invalid, so `multiple_joint_routes` is not a result reason.

`joint_route_id` is non-null only for `multi/explicit_joint_route`. A single or multi result has a non-empty selected set. Every other state has an empty selected set.

## Effective execution

The effective execution binds:

- route caller-request digest;
- corpus snapshot digest;
- routing-policy digest;
- tool identity;
- route algorithm coordinates;
- exact discovery and route limits;
- nested discovery effective-execution digest.

Every matching field in the route result must equal the effective execution. The route result digest covers the complete nested discovery result and all routing evidence.

## Error envelope

Safe error messages are fixed by implementation and contain no path, query, policy content, exception text, or environment value. Error kinds are closed.

- malformed/unknown route request: `invalid_request`;
- malformed, unauthorized-coordinate, digest-invalid, non-canonical, or corpus-inconsistent policy: `invalid_policy`;
- malformed corpus: `invalid_ontology`;
- changed corpus or policy capture: `snapshot_changed`;
- any budget exceeded: `resource_exhausted`;
- runtime/Unicode/schema incompatibility: `incompatible`;
- unsupported adopted identity: `unsupported_identity`;
- otherwise: `internal`.

Errors never carry admission or routing state and never count as successful abstention.

## Capabilities and compatibility

`semantic-route-capabilities.v0` is emitted only by a separate route-capabilities command. Existing discovery capabilities remain byte-identical and do not advertise route schemas or algorithms.

Protected discovery-v0 files and payloads are enumerated in the RFC. Additive changes to global help, README command lists, and command contracts are allowed and are not direct-discovery compatibility failures.
