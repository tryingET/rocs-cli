---
summary: "Decision 104 accepts an owner-bounded semantic-evaluation architecture and rejects one cross-owner global state machine."
read_when:
  - "Designing semantic-evaluation custody, evaluation, or publication integration."
  - "Reviewing Decisions 105, 106, or 107."
type: "adr"
status: "accepted"
decision_id: 104
---
# ADR — Owner-bounded semantic evaluation

- Status: Accepted
- Date: 2026-08-03
- Decision: 104

## Context

Decision 103's R2 candidate at `70d3645e724c93ea407bc11f4e672df7a6ae2289` passed 347 tests but failed independent security review. Caller-authored signatures and proof objects could describe authority and runtime effects they did not enforce.

The first Decision 104 response tried to close every gap with one cross-owner executable state machine. Commit `e43eb045179ba95638e690a9574fdc80fd26de7f` preserves that rejected 271 KB packet. It remained non-constructible and duplicated state belonging separately to the semantic owner, DSPx, ROCS, and Decision 53.

Strict review accepted only the compact owner-boundary packet at:

- commit `a7c291c780be4981ed14f16c8e3ed79f501b9a8f`;
- tree `e8d24279bffb73488bb5bf1b3d4b2ea46f278c59`;
- review memo `docs/project/semantic-evaluation-custody-broker-v1-review-memo.md`;
- controlling synthesis `docs/project/semantic-evaluation-custody-broker-v1-review-synthesis.md`.

Any normative change to the reviewed problem brief, RFC, evidence note, or adjudication retires that closure.

## Decision

Adopt an owner-bounded architecture. Do not define one cross-owner executable state machine.

1. **Semantic owner:** exclusively owns immutable policy meaning, policy identity, provenance, and intent over those bytes.
2. **DSPx:** may own bounded execution episodes and receipt-backed evidence only for effects it actually mediates.
3. **ROCS:** owns deterministic evaluation under semantic-owner-defined meaning, including accepted-contract canonicalization, evidence validation, and verdict derivation. ROCS cannot claim unobserved runtime effects or redefine policy meaning.
4. **Decision 53 authority:** remains the sole owner of semantic-release publication, currentness, adoption, use, and rollback semantics.
5. **AK:** records canonical task, decision, and evidence lineage but creates none of the preceding domain authorities.

Executable state machines may be canonical inside an owner boundary. Cross-owner composition shall use immutable versioned evidence contracts and adversarial interface vectors without reproducing owner-private state.

An enforcement fact is acceptable only from the mechanism that actually mediates the effect. A signature proves intent over bytes; it does not prove process execution, protected-data access, cleanup, publication, or currentness.

## Successor decisions

This ADR accepts boundaries, not successor mechanics:

- Decision 105 must obtain DSPx owner acceptance for the mediated-effect inventory, local execution-episode machine, crash/replay behavior, and receipts.
- Decision 106 must obtain ROCS owner acceptance for evaluation inputs, canonicalization, deterministic derivation, failure classification, and conformance vectors.
- Decision 107 may define only a non-authoritative compatibility contract to Decision 53. It must not assume Decisions 105 or 106 before their owners accept them and cannot duplicate or activate publication/currentness.

Each successor may narrow or reject the assumed integration.

## Explicitly not authorized

This ADR does not authorize:

- implementation of a broker, custody service, evaluation machine, adapter, or verdict register;
- reuse, rerun, relabeling, tuning, patching, or revival of Decision 98 B0 or rejected Decision 103 R2;
- real policy, datasets, protected reads, process execution, provider/model calls, network access, or dogfood;
- publication, currentness, consumer adoption, Pi integration, prompt projection, or automatic preflight;
- treating tests, signatures, receipts, Git commits, AK records, intercom messages, or this ADR as live owner or runtime authority.

Owner-local ADRs and explicit post-ADR implementation tasks remain mandatory before code or live effects.

## Consequences

### Positive

- Authority is assigned to systems that can truthfully enforce or interpret it.
- ROCS no longer needs to simulate DSPx-private runtime state.
- DSPx evidence cannot silently become semantic or publication authority.
- Decision 53 is reused rather than duplicated.
- Owner-local machines can remain executable and adversarially testable without one global graph.

### Costs and unresolved work

- End-to-end behavior is intentionally incomplete until Decisions 105–107 converge.
- Interface compatibility may fail and force a narrower design.
- Cross-owner conformance vectors must be generated from accepted owner contracts rather than maintained as an independent oracle.
- No current implementation demonstrates this architecture.

## Supersession and rollback

This ADR supersedes only Decision 103's combined evaluation proof-graph assumption. It does not erase Decision 103 history, rehabilitate rejected R2, or weaken Decision 53.

Rollback means withholding or superseding this boundary ADR and leaving Decisions 105–107 and all implementation/live effects blocked. Because this ADR authorizes no runtime or publication effect, rollback requires no live-state mutation.
