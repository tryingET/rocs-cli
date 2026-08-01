---
summary: "Evidence, option analysis, and selected boundary for semantic-router-v0."
read_when:
  - "Evaluating alternatives to the current lexical-emission architecture."
type: "exploration"
status: "draft"
---
# Semantic router v0 exploration

## Evidence boundary

Decision 98 B0 is immutable contaminated historical evidence, not unseen or sealed data. This exploration intentionally inspected row-specific IDs and scores to falsify score/margin admission and diagnose the architectural failure class. It does not derive an alias, policy clause, acceptance floor, or implementation fixture from those rows. The frozen B0 corpus, prompts, labels, scores, and report are prohibited development and acceptance inputs for the replacement. Every later participant and clause must carry explicit contamination/provenance records under the validation plan.

The code boundary is equally clear:

- `src/rocs_cli/discovery.py` normalizes query text, scores documents using fixed field weights, emits documents scoring at least `100`, classifies the candidate list, and returns `semantic-discovery-result.v0`.
- `docs/project/semantic-discovery-v0/protocol.schema.json` closes the result shape with `additionalProperties: false` and binds exact algorithm and retrieval vocabularies.
- discovery candidates are evidence, not certified applicability.
- `not_applicable` is currently consumer/adapter policy, not lexical absence.

## Options

### Option A — Tune lexical scores, margins, or candidate thresholds

Reject.

B0 contains high-scoring nulls and weak or missing applicable results. A score floor that excludes low-scoring nulls cannot exclude N02/N04/N05 without also depending on prompt-specific knowledge, and score/margin fitting against B0 would violate preregistration. Candidate count and `low_confidence` are retrieval diagnostics, not admission evidence.

### Option B — Replace lexical discovery with dense retrieval

Reject for v0.

Dense retrieval may improve paraphrase recall, but nearest-neighbor similarity still returns a nearest neighbor. It does not create an open-set admission contract, weakens deterministic auditability, adds an unproven runtime, and would not lawfully open provider/model work after B0 failure.

### Option C — Change `semantic-discovery-result.v0` to include abstention

Reject.

The result is closed, fully digest-bound, and directly consumed. Adding fields, changing retrieval states, suppressing existing candidates, or changing its algorithm identifier is a breaking protocol mutation. Existing discovery must remain a byte-compatible primitive.

### Option D — Consumer-local applicability policy only

Retain as a viable deployment boundary, but insufficient as the sole architecture.

Consumer policy fits the existing authority split and can suppress projection. A purely consumer-local implementation, however, duplicates semantic interpretation, weakens reusable deterministic receipts, and risks different consumers assigning different meanings to the same ontology policy.

### Option E — Separate ontology-policy interpreter in ROCS

Select.

Add an independent `semantic-router-*.v0` protocol and CLI operation. Ontology owners author a closed routing policy. ROCS validates coordinates and evaluates clauses deterministically. The unchanged lexical result remains diagnostic input. Consumers decide whether to project an accepted route but cannot manufacture one from abstained evidence.

This changes no existing discovery claim. It creates a new reviewed semantic contract.

### Option F — Learned or calibrated admission classifier

Defer.

A frozen local classifier could be deterministic at runtime, but it requires a separate calibration owner, independent data, model identity, and stronger drift controls. It is not needed to test the symbolic decomposition and would obscure whether the contract itself is sound.

## Selected decomposition

### Layer 1 — Invocation

Validate request, corpus, routing-policy, runtime, identities, limits, and digests. Invalid, unavailable, incompatible, exhausted, changed-snapshot, and internal outcomes remain errors. They never become successful abstentions.

### Layer 2 — Domain admission

Evaluate explicit positive and exclusion clauses over normalized query tokens.

- Positive only: admitted.
- No positive support: abstained with `no_policy_domain_support`, scoped only to the exact policy/corpus/profile coordinate.
- Exclusion only: abstained with `explicit_domain_exclusion`.
- Both: abstained with `domain_support_exclusion_conflict`.

Lexical candidate scores cannot override admission.

### Layer 3 — Concept support

For an admitted query, evaluate each concept's positive and exclusion clauses.

- positive without exclusion: supported;
- positive plus exclusion: conflicted;
- no positive support: unsupported.

Existing ontology `anti_examples` are not routing exclusions. They explain concept meaning and currently affect lexical score. A routing exclusion is separately authored, typed, reviewed, and digest-bound.

### Layer 4 — Adjudication

- Any supported/excluded conflict: abstain.
- Zero supported concepts: abstain.
- One supported concept: single route.
- Multiple supported concepts route only through one exact owner-authored joint route whose ontology-ID set equals the complete supported set and whose positive clause matches without exclusion.
- Multiple supported concepts without that exact joint route are ambiguous and select nothing.

V0 rejects inferred independent-evidence heuristics. Multi-intent is explicit policy meaning rather than code inference.

### Layer 5 — Candidate diagnostics

Derive and execute unchanged `rocs-lexical-v0` exactly once and nest its complete unchanged result. Symbolic support remains separate routing evidence; the router does not fabricate score-zero discovery candidates. Scores and margins never authorize admission or selection.

### Layer 6 — Consumer projection

A consumer validates the router result and may:

- render selected concepts;
- suppress even an admitted route under stricter local policy;
- present abstention or ambiguity to the operator.

A consumer may not convert abstention into routing or reinterpret operational errors as benign abstention.

## Proposed policy grammar

`semantic-routing-policy.v0` is a closed object containing:

- exact policy, authority/provenance, and domain identity;
- Unicode and normalization coordinates;
- domain `admit_any` and `exclude_any` clauses;
- per-concept `support_any` and `exclude_any` clauses;
- explicit joint routes with non-empty positive clauses;
- a canonical policy digest.

A clause is a conjunction of groups. Each group is a disjunction of exact normalized token or contiguous phrase alternatives. No stemming, embeddings, inferred synonyms, ambient stopword list, or floating-point score exists in v0.

Paraphrase alternatives may come only from reviewed ontology meaning and independent development material. They may not be copied from B0 to make B0 pass. Every policy change creates a new digest and requires new sealed evidence.

## Proposed result boundary

Use a separate `semantic-route-result.v0` with its own digest domain. It contains:

- request, corpus, policy, tool, and effective-execution identities;
- algorithm identity `rocs-symbolic-router-v0` and candidate algorithm `rocs-lexical-v0`;
- admission state, closed reason, support clauses, and exclusion clauses;
- routing state, closed reason, selected/supported/conflicted concept IDs;
- canonical witness evidence;
- the complete nested unchanged `semantic-discovery-result.v0`;
- result digest covering all routing and nested lexical evidence.

Router abstention suppresses selection, not historical lexical evidence. A bare lexical-result digest is rejected because no immutable content store or availability contract exists.

## Compatibility implications

Additive implementation likely requires new modules for policy parsing, router protocol/invariants, router execution, and CLI adaptation. Existing integration additions include CLI parser registration, command contracts, README parity, generated package convergence, and new independent Python/Node golden verification.

Existing discovery schema, generated embedding, digest domains, golden fixtures, differential fixtures, implementation, and tests are compatibility anchors and must remain byte-identical unless a separate decision explicitly authorizes otherwise.

## Closed design choices

1. Development uses a descriptor-anchored exact policy file with owner/provenance coordinates. Only conspicuously synthetic policy is allowed in ROCS implementation fixtures. Production publication remains an exact semantic-owner action.
2. Multi-route meaning is expressed only by explicit owner-authored joint routes; code does not infer independent intent.
3. V0 always derives and nests one unchanged lexical result, including on policy abstention.
4. ROCS owns reusable schema/interpreter mechanics. Exact ontology owners own every non-synthetic policy instance and publication decision.
5. Cumulative resource, matching-work, result-byte, witness, clause, group, and alternative bounds are closed in the normative schema and invariants.

## Recommended decision

Authorize a development-only, additive symbolic router protocol and interpreter in ROCS. Preserve lexical discovery unchanged. Require a separate owner-authored policy and a new uncontaminated validation program before any Pi integration or automatic prompt projection.
