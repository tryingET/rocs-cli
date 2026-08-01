---
summary: "Accept a development-only deterministic abstaining semantic router over unchanged lexical discovery evidence."
read_when:
  - "Implementing or reviewing Decision 102."
type: "adr"
status: "accepted"
decision_id: 102
---
# ADR — Development-only abstaining semantic router v0

- Status: Accepted
- Date: 2026-08-01
- Decision: 102

## Context

Decision 98 B0 proved that deterministic lexical discovery can retrieve relevant concepts while catastrophically over-routing null inputs. The frozen run achieved recall@3 `0.90`, deterministic repeat `1.00`, and low latency, but failed MRR and null rejection (`0.10` versus `0.90`). High-scoring nulls and weak applicable prompts falsified global score or margin thresholds as an admission mechanism.

The accepted discovery protocol already states that candidates are evidence rather than certified relevance. The defect was architectural: domain admission, candidate generation, semantic adjudication, operational error, and consumer projection were conflated.

Decision 102's strict review converged on exact packet:

- packet commit: `52454f5dd86582290db642b73acc6c5cab8e9e1d`;
- packet tree: `f38eff588a1bae4af00cb411fab423713623bcec`;
- packet aggregate: `417ee5c7148573f80b841a0ae0d22f12ab8152c020c765f9a2a32976a001ba53`;
- packet manifest SHA-256: `0fad833e48d6d2c198ee4f5f8c39d6fea67d59a20a758969b623dbe44fd09d68`;
- final review memo/synthesis commit: `73f74bb9a6af31cdbe82791fcfbb61ee596c5d17`.

Final lanes:

- semantic authority: `dispatch-1785603595275` — accept;
- protocol/security: `dispatch-1785603595275-1` — accept;
- empirical falsification: `dispatch-1785603595276` — accept.

## Decision

Implement an additive, development-only `semantic-route` protocol and deterministic symbolic interpreter in ROCS.

The implementation shall:

1. preserve `semantic-discovery-result.v0`, `rocs-lexical-v0`, protected discovery files, digests, capabilities, golden fixtures, and direct CLI behavior;
2. add separate route request, routing-policy, provenance, effective-execution, result, capability, error, schema, invariant, and digest domains;
3. require explicit positive policy support for domain admission and concept selection;
4. use explicit owner-authored joint routes for multi-concept selection;
5. abstain without selected IDs on absent policy support, conflict, or unsupported multiplicity;
6. preserve operational errors as errors;
7. derive and execute unchanged lexical discovery exactly once and nest its complete result;
8. bind every policy alternative to exact provenance and contamination records;
9. remain offline, deterministic, bounded, descriptor-anchored, and digest-addressed;
10. use only conspicuously synthetic policies within Decision 102 implementation tasks.

Synthetic-only is an AK/Decision/task authorization boundary, not a property inferred by the protocol. Mechanically valid v0 results are development evidence only and convey no ontology-owner approval, publication, adoption, consumer activation, or prompt-projection authority.

## Authorized scope

This ADR authorizes only ROCS-owned development mechanics:

- normative route schema embedding;
- canonical JSON/digest helpers specific to route domains;
- sequence-preserving route tokenizer;
- policy/provenance parsing and validation;
- symbolic clause matching and evidence;
- admission/routing state machines;
- nested unchanged lexical result;
- route CLI and capabilities;
- synthetic fixtures, independent verifier, compatibility checks, and repository tests;
- README and command-contract additions required by the implementation.

## Explicitly not authorized

- changing existing discovery-v0 protected surfaces;
- tuning or rerunning Decision 98 B0;
- authoring or executing a non-synthetic owner policy under Decision 102;
- defining an adopted-policy/publication/currentness protocol;
- D/U/O empirical execution;
- semantic-owner publication;
- consumer shadowing;
- Pi integration or prompt projection;
- provider/model or behavioral-benefit claims.

Each later effect requires its own owner-reviewed protocol, task, decision, and evidence.

## Consequences

### Positive

- Applicability becomes explicit policy evidence rather than accidental nearest-match behavior.
- Lexical discovery remains stable, auditable evidence.
- Abstention, ambiguity, errors, and selection become structurally distinct.
- Policy meaning remains outside ROCS while interpretation remains reusable and deterministic.
- Future empirical evidence can test false routing and useful coverage without contaminating B0.

### Costs

- A second protocol family and generated schema must be maintained.
- Symbolic clauses require owner provenance and can abstain on unknown paraphrases.
- Real adoption requires a future publication/currentness protocol and substantial independent data custody.
- The implementation cannot claim product benefit from synthetic fixtures.

## Validation

Implementation acceptance requires:

- exact protected discovery baseline matches;
- new schemas and invariants validated in Python and independent Node code;
- deterministic byte-identical repeats;
- closed safe errors and resource exhaustion;
- descriptor-anchored policy/provenance capture;
- full repository gate;
- independent implementation review.

The future D/U/O evidence contract remains defined by the accepted packet but is not authorized by this ADR.

## Rollback

Revert the additive implementation commit. Existing discovery remains unchanged and requires no migration. Preserve failed fixtures, reports, and decision evidence. Do not rewrite B0 or policy history.

## Supersession

Any adopted-policy support, learned admission, dense retrieval, real ontology policy, consumer shadow, or prompt projection requires a new decision and may supersede only the relevant development boundary—not the historical evidence or unchanged discovery protocol.
