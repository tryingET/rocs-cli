---
summary: "Post-ADR implementation sequence for Decision 53's immutable semantic release protocol and one named-canary boundary."
read_when:
  - "Implementing Decision 53 after its accepted ADR."
  - "Creating or reviewing semantic-release execution tasks."
type: "implementation_plan"
status: "accepted_plan"
---
# Implementation Plan — Semantic Release and Single-Canary Adoption

## Authority and limit

- AK decision: `53`
- ADR: [`../adr/2026-07-13-semantic-release-and-single-canary-adoption.md`](../adr/2026-07-13-semantic-release-and-single-canary-adoption.md)
- Accepted protocol: [`semantic-release-capsule-and-consumer-adoption-protocol-v0.md`](semantic-release-capsule-and-consumer-adoption-protocol-v0.md)
- Accepted machine revision: [`semantic-release-revision-v13.md`](semantic-release-revision-v13.md)
- Controlling review closure: [`semantic-release-rereview13-final-synthesis.md`](semantic-release-rereview13-final-synthesis.md)

This plan authorizes implementation of the accepted, default-off protocol substrate after Decision 53 is authoritatively unblocked. It does not itself issue any semantic-owner fact, consumer consent, recovery-controller appointment, canary name, release approval, publication, activation, delivery claim, or fleet/default authority.

`live_acquisition_implemented=false` remains mandatory through I1–I5. Changing it requires the separately reviewed G1 gate below and complete owner-issued evidence.

## Preconditions

Before any implementation task is claimable:

1. this plan, the companion validation/rollout/rollback plan, and the owner-scoped cross-repo fan-out are committed and attached to Decision 53;
2. each executable task is owner-scoped with exact repo-relative scope and guardrails, linked as `post_adr_execution`, and explicitly reevaluated;
3. Decision 53 is `unblocked` in AK;
4. the target worktree is clean or the owner provides an isolated clean worktree that preserves concurrent work;
5. exact dependencies and evidence references resolve through AK, not through prose or fixture claims.

The current dirty `core/ontology-kernel`, `softwareco/owned/agent-kernel`, and `softwareco/owned/pi-extensions` worktrees must not be overwritten or mixed into Decision 53 work.

## Execution sequence

### I1 — ROCS protocol substrate

Owner: `core/rocs-cli`

- Import the accepted closed schemas, registries, authority edges, digest links, and invariants into small deterministic runtime modules.
- Preserve independent Python and Node conformance without either validator importing the other.
- Add typed models for coordinates, owner-store receipts, capability pins, publication history, consumer intent/acceptance, materialization, activation, generation, delivery, evidence, and rollback.
- Keep all production actions unreachable; this slice validates proposal objects and deterministic derivations only.

Gate: committed fixtures regenerate byte-identically; Python and Node accept/reject the same corpus; the full ROCS gate passes offline.

### I2 — ROCS transactional state machines

Owner: `core/rocs-cli`

- Implement append-only, canonical-head/CAS publication, materialization, activation-input, generation-input, and rollback verification primitives.
- Keep receipt/history roots outside replaceable semantic and runtime roots.
- Implement bounded no-follow reads, closed environments, one end-to-end deadline, input/output/depth limits, mutation descriptors, and typed failure receipts.
- Add crash-point, replay, stale-head, revocation, supersession, partial-failure, and idempotency tests.
- Do not provision live acquisition capabilities and do not publish or activate anything.

Gate: exhaustive fault injection preserves or restores the exact preimage; no test mutates an owner repository, managed `dist/`, or network state.

### I3 — Semantic-owner sandbox contracts

Owner: `core/ontology-kernel`

- After the existing dirty worktree is reconciled, implement sandbox-only namespace policy, owner predicates, compatibility/lifecycle decisions, trust rotation/revocation, release approval, and publication/withdrawal/revocation record production.
- Keep authored ontology bytes and semantic-owner facts in the owner surface; ROCS receives only explicitly pinned local acquisition inputs.
- Use disposable stores and non-production keys/identities. Do not mutate the canonical ontology or a production publication head.

Gate: semantic-owner fixtures and owner-store read receipts are independently replayable; clean-source and complete-tree checks pass; `live_acquisition_implemented=false` remains true.

### I4 — AK lineage coordination

Owner: Agent Kernel runtime; target repository `softwareco/owned/agent-kernel` with an empty file-mutation scope.

- Record only canonical task, decision, dependency, prerequisite, stop-fact, and evidence lineage.
- Enforce direct equality of each resolved reference ID, observed task ID, capability-pin role suffix, and decoded AK receipt task ID.
- Preserve target-repository metadata without transferring task authority to ROCS, the semantic owner, the consumer, or Pi.
- Do not edit the dirty Agent Kernel worktree as part of this slice.

Gate: AK receipts resolve exact task IDs and current store heads; no ontology bytes or semantic-owner/consumer-owner facts enter AK.

### I5 — Default-off Pi delivery adapter

Owner: `softwareco/owned/pi-extensions/packages/pi-ontology-workflows`

- After the owner provides a clean worktree, implement protocol validation and exact delivered/suppressed/failed attestations for the accepted consumer/canary scope.
- Reuse Decision 52 prepared-runtime safety only where the accepted Decision 53 identities and authority graph validate exactly.
- Keep all production behavior default-off. Pi cannot issue consumer acceptance, activation, semantic approval, or influence evidence.
- Preserve cancellation, stale-result rejection, lifecycle invalidation, fixed argv, closed environment, bounded teardown, and structural-only automatic prompt content.

Gate: hostile issuer, stale-head, scope-drift, cancellation, timeout, and marker-forgery tests fail closed; existing default search/startup behavior is unchanged.

### I6 — Owner and runtime identity establishment

Coordination owner: Decision 53 execution task in `core/rocs-cli`; fact issuance remains with each named owner.

Before a live gate can be proposed, establish without substitution:

- the exact `softwareco/pi-canary-consumer` repository identity revision `3` and its consumer owner;
- one operator-named canary and explicit consumer-owner consent;
- a concrete independently owned and pinned recovery controller outside active semantic/runtime roots;
- the production Pi adapter repository identity accepted by the protocol;
- owner-specific capability distribution and local authenticated store-read designs.

The named consumer and recovery-controller repositories are not currently present. This slice may document and verify owner decisions, but it must not create a substitute identity, infer consent, or widen protocol v0.

Gate: every owner and canonical locator exists, is independently governed, and matches the accepted protocol exactly. Any identity change requires a superseding decision/protocol rather than an implementation shortcut.

## Separately reviewed live gates

### G1 — Live acquisition implementation

A fresh owner/ROCS/governance/security review must approve the concrete capability distribution, authenticated local owner-store reads, terminal trust pins, currentness behavior, key handling, deadlines, and revocation response. Only this gate may change `live_acquisition_implemented` to `true`.

### G2 — Sandbox end-to-end proof

With G1 evidence, run a disposable, offline, non-production proof of owner acquisition → deterministic ROCS verification → materialization → consumer acceptance → activation candidate → generation/delivery attestations → every rollback class. No production head or consumer default changes.

### G3 — Semantic publication

Requires exact semantic-owner release approval, compatibility/lifecycle decision, trust/currentness evidence, clean immutable source, complete capsule/projection/archive equality, and publication CAS/recovery proof. Publication does not authorize adoption.

### G4 — One named-canary adoption

Requires the exact revision-3 consumer, explicit consumer intent and acceptance, operator-named canary, predeclared locally available rollback targets, independent recovery-controller availability, and an action-time complete authority graph. Activation does not authorize a second consumer, startup/default behavior, or fleet rollout.

### G5 — Evidence and closeout

Record immutable AK evidence for each task and operation, independently replay the receipts, rehearse rollback, and crystallize KES learning. Empirical DSPx/Oracle analysis remains a later owner-scoped activity after enough traces exist.

## Dependencies

- I2 depends on I1.
- I3, I4, and I5 depend on I1 and may proceed in parallel only in clean owner worktrees.
- I6 depends on accepted owner decisions and cannot be satisfied by fixture identities.
- G1 depends on I2–I6 and a fresh review.
- G2 depends on G1.
- G3 and G4 are separate authority operations; G4 depends on an exact published release but publication never implies adoption.
- G5 depends on all executed slices and does not promote defaults or fleet policy.

## Deferred beyond protocol v0

A second consumer or canary, repository rename, explicit-search default, automatic-preflight default, startup orientation, mandatory enforcement, fleet rollout, signing infrastructure expansion, or protocol widening requires a new decision and superseding protocol. Passing this plan's gates cannot authorize those changes.
