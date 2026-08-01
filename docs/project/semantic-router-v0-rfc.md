---
summary: "RFC for an additive deterministic abstaining semantic router over unchanged ROCS lexical evidence."
read_when:
  - "Reviewing the semantic-router-v0 architecture decision."
type: "rfc"
status: "proposed"
---
# RFC — Deterministic abstaining semantic router v0

## Status and authorization boundary

Proposed for strict multi-lane review. This draft authorizes no implementation.

If recorded as an accepted ADR, it authorizes only a development-only ROCS protocol, schema embedding, deterministic interpreter, CLI, synthetic fixtures, and compatibility tests. It does not authorize:

- a concrete non-synthetic ontology routing policy;
- semantic-owner publication or adoption;
- D/U/O empirical execution;
- consumer or Pi integration;
- a shadow run;
- prompt projection.

Decision 102 is cross-repo because the proposed contract touches ontology policy authority, ROCS interpretation, empirical custody, and eventual consumer projection. Every owner-local effect after the ROCS development implementation requires its own authorized task and owner gate.

## Decision

Add a separate development-only `semantic-route` operation with new request, policy, effective-execution, result, capabilities, error, invariant, and digest domains. The router evaluates exact owner-provenanced symbolic routing policy and nests the complete unchanged `semantic-discovery-result.v0` as diagnostic candidate evidence.

## Normative bundle

- `docs/project/semantic-router-v0/protocol.schema.json`;
- `docs/project/semantic-router-v0/invariants.md`;
- this RFC.

The schema and invariant document close the object shapes, digest preimages, ordering, matching, state/reason matrices, resource accounting, filesystem capture, and lexical lineage.

## Core invariants

1. Router admission and selection require explicit positive policy evidence.
2. Lexical score, margin, candidate count, and retrieval classification never authorize routing.
3. No positive domain support means `no_policy_domain_support` under the exact policy coordinate—not a universal out-of-domain claim.
4. Operational failures remain errors and never become abstention.
5. Existing discovery protocol and behavior remain protected compatibility anchors.
6. Ontology/semantic owners author and approve meaning; ROCS validates and interprets bytes.
7. Consumers may suppress a route but may not override abstention, manufacture selected IDs, or rerank silently.
8. B0 is contaminated historical diagnosis and never fresh router evidence.
9. V0 has no provider, model, embedding, network, learned component, or automatic prompt projection.

## Authority split

| Concern | Owner |
|---|---|
| Concrete policy clauses, meaning, review, publication, withdrawal | exact ontology/semantic owner, normally `core/ontology-kernel` or the policy-owning ontology repo |
| Policy language mechanics, schema, validation, deterministic interpretation, receipts | ROCS |
| Adopted corpus-policy publication coordinate | semantic owner through its accepted publication/release process |
| Empirical U/O custody and independent analysis | DSPx/Oracle or another named independent empirical owner |
| Adoption intent, suppression policy, activation, deactivation, rollback | exact consumer owner |
| Bounded invocation, timeout, rendering, delivery/suppression/failure attestation | Pi owner where Pi is the consumer runtime |
| Decisions, tasks, evidence, lineage, coordination | AK/governance |

AK records authority movement; it does not own rollout or rollback behavior. A local file path and digest prove byte identity, not semantic-owner approval.

## Development policy boundary

ROCS development may use only conspicuously synthetic policies carrying exact repository, revision, path, content digest, and review-reference coordinates. Synthetic fixtures assert grammar behavior, not real-domain authority.

Any non-synthetic policy requires:

- exact semantic-owner repository and revision;
- owner-controlled path and content digest;
- owner review fact;
- separate owner task;
- owner publication/adoption gate before consumer use.

## Protocol family

New schemas:

- `semantic-route-request.v0`;
- `semantic-routing-policy.v0`;
- `semantic-route-effective-execution.v0`;
- `semantic-route-result.v0`;
- `semantic-route-capabilities.v0`;
- `semantic-route-error.v0`.

New algorithms:

- router: `rocs-symbolic-router-v0`;
- candidate algorithm: exactly `rocs-lexical-v0`.

New digest separators and preimages are specified in the invariant document. Existing discovery and pack digest domains do not change.

## Request and CLI

The closed request contains:

- schema and raw query;
- corpus identity selector and profile;
- exact router and candidate algorithms;
- mandatory expected routing-policy digest;
- separate discovery and route limits.

The router derives the legacy discovery request mechanically as specified in the invariants.

Development CLI:

```text
rocs route \
  --repo <corpus-root> \
  --routing-policy-root <existing-local-directory> \
  --routing-policy <root-relative-file> \
  --request-json - \
  --tool-kind development_runtime \
  --tool-manifest-digest sha256:<digest> \
  --json --no-index-cache --no-env-file
```

Automatic use is stdin-only. Policy capture is descriptor-anchored and no-follow. Ref resolution is disabled. Any future ref support requires explicit workspace root, strict mode, and separate authorization. No network resolver exists.

## Routing policy

The closed policy binds:

- policy identity;
- Unicode, normalization, and sequence-tokenization coordinates;
- exact provenance/owner coordinates;
- domain positive and exclusion clauses;
- per-concept positive and exclusion clauses;
- explicit joint routes;
- canonical policy digest.

All arrays must arrive in canonical order and all IDs must be unique under the invariant document. ROCS rejects rather than repairs non-canonical policy input.

### Clause grammar

A clause is a conjunction of named groups. A group is a disjunction of exact canonical token or contiguous phrase alternatives.

- `token`: exactly one canonical sequence token;
- `phrase`: at least two canonical tokens joined by one ASCII space;
- group succeeds when one alternative matches;
- clause succeeds when every group matches;
- `*_any` succeeds when one clause matches.

There is no stemming, regular expression, inferred synonym, ambient stopword list, numeric weight, embedding, or learned component.

### Anti-examples and routing exclusions

Ontology `anti_examples` remain conceptual meaning and lexical diagnostic evidence. They never become router exclusions automatically.

A routing exclusion is a distinct owner-authored clause with its own ID, provenance, review, and policy digest. Deriving one from an anti-example is an explicit semantic-owner act.

### Joint routes

Multi-concept selection is explicit. Every joint route:

- identifies two to eight policy concepts;
- has non-empty positive clauses and a required, possibly empty, exclusion list;
- has an ontology-ID set unique within the policy.

Multiple supported concepts route only when one exact joint-route ontology-ID set equals the complete supported set, its positive clause matches, and no exclusion matches. Otherwise the result is ambiguous or abstained according to the invariant matrix.

## Matching and witnesses

Route matching uses a new sequence-preserving tokenizer. It must not reuse discovery's deduplicating token helper for witness positions.

Coordinates:

1. Unicode 15.0.0 NFKC;
2. full casefold;
3. whitespace collapse;
4. maximal contiguous Unicode Letter or Number token sequence retaining duplicates.

The invariant document defines canonical alternatives, token indices, witness selection, array order, and evidence order.

## Evaluation

1. Capture policy and corpus with exact identity and mutation checks.
2. Validate request, policy, algorithms, limits, tool identity, corpus references, and digests.
3. Derive and execute unchanged discovery exactly once.
4. Normalize/tokenize the route query once.
5. Evaluate domain positive and exclusion clauses.
6. Abstain on no policy support, explicit exclusion, or domain conflict.
7. For admitted queries, evaluate concept positive and exclusion clauses.
8. Abstain on concept support/exclusion conflict.
9. Route one supported concept directly.
10. Route multiple supported concepts only through one exact explicit joint route.
11. Otherwise abstain or remain ambiguous.
12. Construct the effective execution and result, nest the complete discovery result, validate invariants, enforce limits, and digest.

No lexical score influences steps 5–11.

## Result and lineage

The result contains:

- route request, corpus, policy, tool, algorithm, and effective-execution identities;
- admission state/reason and clause evidence;
- routing state/reason, supported/conflicted/selected IDs, and joint-route identity;
- deterministic witnesses;
- the complete unchanged nested `semantic-discovery-result.v0` including its digest;
- route result digest.

There is no digest-only lexical reference, external result store assumption, or score-zero discovery candidate. Symbolic support is represented by routing evidence and IDs, not by fabricating a lexical candidate.

Operational errors use a separate safe route error envelope and contain no routing state.

## Resource limits

Hard maxima are closed in the route schema:

| Resource | Maximum |
|---|---:|
| Policy bytes | `1,048,576` |
| Concepts | `1,000` |
| Total clauses | `4,096` |
| Groups per clause | `8` |
| Alternatives per group | `16` |
| Total alternatives | `16,384` |
| Total normalized alternative bytes | `524,288` |
| Joint routes | `1,000` |
| Concepts per joint route | `8` |
| Evidence entries | `2,048` |
| Witnesses | `8,192` |
| Matching work | `2,000,000` |
| Route result bytes | `262,144` |
| Parser depth | `32` |
| Collection items | `20,000` |

The inherited discovery limits remain independently bounded. The invariant document defines cumulative accounting. Any exhausted budget is an error.

## Protected compatibility inventory

The following discovery-v0 surfaces must remain byte-identical in the implementation candidate:

- `docs/project/semantic-discovery-v0/protocol.schema.json`;
- `src/rocs_cli/_semantic_discovery_schema.py`;
- existing discovery golden fixtures;
- existing discovery differential fixtures;
- existing `discover-capabilities` payload bytes;
- existing direct `rocs discover` stdout, stderr, and exit behavior for the frozen compatibility corpus;
- existing discovery digest separators and preimages.

New route support uses a separate schema bundle and generated embedding. Additive changes to global `rocs --help`, README command listings, and `rocs contracts` are allowed and are not direct-discovery compatibility failures. Existing discovery capabilities gain no route values.

## Validation and activation boundary

The companion validation plan defines contaminated B0 treatment, D development, U/O custody, anti-leakage, metrics, and one-shot evidence.

An accepted ADR permits only ROCS synthetic development implementation. It does not permit D policy authoring by ROCS, U/O access, release publication, consumer shadowing, or Pi integration.

Later stages require separate owner tasks:

1. ontology-owner policy authoring and review;
2. independent D/U/O custody and preregistration;
3. one-shot U/O execution and review;
4. semantic-owner publication/adoption;
5. consumer-owner no-injection shadow authorization;
6. separate prompt-projection decision.

No stage is implied by the previous stage.

## Alternatives rejected

- score/margin threshold tuning;
- in-place discovery protocol changes;
- dense retrieval as admission;
- consumer-specific hidden semantic heuristics;
- operational failures represented as abstention;
- B0 used as fresh acceptance evidence;
- inferred multi-intent without an owner-authored joint route.
