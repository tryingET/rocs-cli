---
summary: "Decision 104 boundary RFC separating semantic policy, DSPx execution evidence, ROCS evaluation, and Decision 53 publication authority."
read_when:
  - "Reviewing Decision 104 or any successor to Decision 103's combined evaluation proof graph."
type: "rfc"
status: "proposed"
decision_id: 104
---
# RFC — Owner-bounded semantic evaluation architecture

## Status

Proposed for Decision 104 strict convergence. This RFC grants no implementation, execution, publication, adoption, or live-effect authority.

Rejected R2 commit `70d3645e724c93ea407bc11f4e672df7a6ae2289` remains immutable negative evidence. Commit `e43eb045179ba95638e690a9574fdc80fd26de7f` preserves the rejected 271 KB Decision 104 global-machine draft; that draft is not normative.

## Decision

Separate the architecture by source owner. Do not define one cross-owner executable state machine.

```text
semantic owner                 DSPx                         ROCS
immutable policy meaning  ->  execution episode evidence -> deterministic evaluation
                                                               |
                                                               v
                                Decision 53 publication/currentness
```

Each owner may define an executable machine for state it actually controls. Cross-owner composition uses versioned immutable evidence contracts and adversarial conformance vectors. No component may recreate another owner's internal state as its own authority.

## Authority boundaries

| Boundary | Owns | Does not own |
|---|---|---|
| Semantic owner | Immutable policy coordinate, semantic meaning, provenance, candidate identity, and explicit owner intent over those bytes | Dataset custody, process execution, evaluation observations, verdict publication, or currentness |
| DSPx | Bounded execution episodes and receipt-backed empirical/runtime evidence for effects it actually mediates | ROCS semantic truth, publication/currentness, consumer adoption, or governance approval |
| ROCS | Semantic contracts, canonicalization, deterministic evaluation rules, evidence validation, and verdict derivation under an accepted ROCS contract | Claiming unobserved runtime effects, starting processes, controlling protected data, or publishing current releases |
| Decision 53 authority | Append-only semantic release publication, currentness, adoption, use, and rollback semantics already accepted by Decision 53 | Redefining policy meaning, execution custody, or evaluation mechanics |
| AK | Canonical task, decision, and evidence lineage | Semantic truth, runtime enforcement, evaluation, or publication effects |

## Cross-owner invariants

1. **Enforcement facts originate at the effect boundary.** Process start, dataset access, lease/revocation, cleanup, and similar facts are accepted only from the owner mechanism that actually mediates them.
2. **Signatures prove intent over bytes, not runtime behavior.** A signed policy, request, receipt, or verdict cannot substitute for an enforced transition.
3. **Executable machines are owner-local.** DSPx and ROCS may each define one canonical executable machine for their own state. Decision 104 defines no global transition graph.
4. **Evidence flows one way.** A consumer may validate immutable evidence but may not use validation to rewrite producer history or acquire producer authority.
5. **Composition is contract-tested.** End-to-end conformance uses accepted interface schemas, generated vectors, and hostile traces from owner contracts; it does not duplicate owner-private state.
6. **Publication remains external.** No evaluation state is itself published or current. Any later publication must enter Decision 53 through a separately accepted compatibility contract.
7. **Rejected evidence stays rejected.** Decision 98 B0 and Decision 103 R2 may not be rerun, relabeled, tuned, patched into acceptance, or used as implementation authority.
8. **Default-off remains mandatory.** No real policy, dataset, process, provider/model, network, Pi integration, publication, consumer adoption, or automatic preflight follows from this decision.

## Successor decision obligations

Decision 104 establishes boundaries only. It deliberately leaves three questions to separate strict decisions:

1. **Decision 105 — DSPx custody/execution:** Which effects DSPx can truthfully mediate, its local execution-episode state machine, crash/replay behavior, and receipt contract.
2. **Decision 106 — ROCS evaluation:** The canonical evaluation inputs, deterministic transition/derivation semantics, failure classification, and generated conformance vectors.
3. **Decision 107 — Decision 53 compatibility:** The minimal non-authoritative adapter by which an accepted evaluation verdict may be referenced without duplicating publication/currentness.

Each successor must be reviewed by its actual owner. Decision 107 must not assume Decision 105 or 106 behavior before those owners accept it. A successor may narrow or reject the assumed integration. Silence, missing owner acceptance, green tests alone, or a prose-only proxy is not convergence.

## Explicit non-goals

Decision 104 does not specify:

- broker data structures, global allocation, sparse-Merkle stores, transaction envelopes, process supervisors, read spools, leases, or verdict registers;
- ROCS field-level schemas, digest registries, branch counts, gate formulas, or operator registries;
- publication records, current-head selection, consumer activation, or rollback machinery already owned by Decision 53;
- implementation sequencing, source changes, test fixtures, deployment, dogfood, or production use.

Those details belong only in accepted owner-local decisions where they are necessary.

## Acceptance and supersession

Strict review of Decision 104 asks only whether the authority partition, invariants, and successor split are correct and stranger-readable. It must not demand implementation detail from the successor decisions.

If accepted through a superseding ADR, Decision 104 supersedes only Decision 103's combined evaluation proof-graph assumption. It does not erase Decision 103 history, rehabilitate rejected R2, weaken Decision 53, or authorize implementation. Owner-local ADRs and explicit post-ADR tasks remain required before any code or live effect.

## Rationale

The controlling adjudication is [`semantic-evaluation-custody-broker-v1-greats-adjudication.md`](semantic-evaluation-custody-broker-v1-greats-adjudication.md). Its result is contextual dominance: state-machine rigor within owner boundaries, security-kernel enforcement at real effect boundaries, information hiding between owners, and evolutionary sequencing across decisions.
