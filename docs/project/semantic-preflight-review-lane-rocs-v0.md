---
summary: "Decision:52 strict review lane for ROCS determinism, corpus identity, protocol closure, effects, and portability."
read_when:
  - "Reviewing decision:52 attempt 1 findings."
  - "Revising the semantic discovery protocol before ADR."
type: "review_memo"
decision_id: 52
review_outcome: "revise_rfc"
---

# Review Lane — ROCS Determinism and Protocol

## Review identity

- Decision: `52`
- Primary: `semantic-discovery-protocol-v0.md@71a7fdc1bfaaa89e266b123fd9ca5a02fca2144e`
- Companion: `semantic-preflight-adapter-v0.md@f4941909fc2a74128648155b23e078cde0a2c0b2`
- Procedure: Prompt Vault `review-rfc-multi`
- Role: corpus identity, algorithm, effects, command contract, and portability

## Verdict

```text
review_outcome = revise_rfc
```

The direction is viable, but strict convergence is not met.

## Lens 1 — Corpus identity and provenance

### Must-fixes

1. Split corpus identity from execution identity. The same corpus must not acquire a new snapshot identity merely because query limits or truncation changed.
2. Specify canonical JSON, hash domains, omitted-field rules, digest spelling, snapshot-manifest framing/order, logical-path encoding, document-byte definition, and development tool/source digest behavior.
3. Define the complete enumeration/capture/revalidation procedure for manifests, profiles, layer order, refs, directory membership, and documents. State the portability limit honestly if atomic generation capture cannot be proven.
4. Close discovery-to-pack lineage. Current exact-ID pack rereads mutable files and cannot prove that it returns the document discovered earlier. Require a digest/snapshot precondition or emit and verify a fresh pack identity.

### Architecture-shaping question

What exactly does `semantic_identity.digest` identify: corpus, execution, or both? The revised RFC must choose separate coordinates rather than overload one digest.

## Lens 2 — Lexical semantics, limits, and errors

### Must-fixes

1. Make `rocs-lexical-v0` normatively reviewable: exact fields/types, normalization, whitespace, tokens/phrases, duplicate behavior, scoring aggregation, integer bounds, evidence order, thresholds, empty query, retrieval-state precedence, and tie-breaks.
2. Resolve Unicode-data drift. Pin one table/version and reject incompatible runtimes, or version compatibility/goldens by Unicode table.
3. Publish a closed limits table: defaults/ranges, pre/post-normalization byte measurement, manifest/profile accounting, parser limits, result-size accounting, and fixed-envelope overflow.
4. Publish a closed machine error schema, kind enum, exit mapping, stream rules, safe detail fields, and failure digest behavior.

### Material improvement required by strict mode

Add metamorphic conformance cases for corpus-order invariance, top-K monotonicity, locale/environment invariance, one-byte mutation, equivalent request encodings, and Python/TypeScript differential validation.

## Lens 3 — CLI contract, effects, and portability

### Must-fixes

1. Define a complete JSON transport such as `--request-json -` or `--request-file`, plus normative convenience-flag mapping and precedence.
2. Choose the protocol-negotiation owner surface: command-contract schema bump, dedicated discovery-capabilities operation, or authenticated runner descriptor.
3. Freeze automatic invocation argv, cache disablement, environment, offline/runtime-prepared posture, bytecode/temp/cache behavior, and schema-3 effects.
4. Define the v0 support matrix and canonical behavior for OS, filesystem, path separators, filename normalization, case sensitivity, symlinks/reparse points, metadata checks, locale, Python, and Unicode. Unsupported environments must return `incompatible`.

## Cross-cutting contradictions

- Snapshot-bound discovery currently hands off to unbound mutable pack retrieval.
- Unicode version is included in output while cross-runtime equality is required.
- A closed JSON request is proposed without a closed CLI transport.
- Automatic no-effect behavior is claimed without an executable environment/effect contract.

## Evidence limits

No implementation, cross-runtime golden suite, filesystem-race proof, or differential verifier exists yet. Current code demonstrates the seams and contradictions but cannot validate the target behavior.

## Legal recommendation

Revise the primary and companion RFCs together, then run a fresh review attempt. Do not draft an ADR or implement discovery from this revision.
