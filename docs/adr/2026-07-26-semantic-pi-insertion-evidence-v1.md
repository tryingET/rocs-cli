---
summary: "Accepts a compact insertion-only Pi evidence protocol and retires the unimplementable semantic-delivery super-protocol direction."
read_when:
  - "Implementing or reviewing semantic Pi prompt-chain insertion evidence."
type: "adr"
status: "proposed"
decision_id: 85
---
# ADR — Semantic Pi insertion evidence v1

## Status

Proposed for Decision 85 after strict five-lane convergence.

## Context

Decision 53 v0 used a fictional `pi-adapter` identity and local callback completion as delivery evidence. Decisions 71, 80, and 82 progressively corrected identity, pinned Unicode-source parsing, and the missing `preimage_kind` registry vocabulary before implementation exposed broader schema/edge/fixture compiler underdetermination. Their implementation tasks `4230`, `4250`, and `4278` failed closed. Decision 84 task `4298` then proved that completing the broad delivery protocol requires at least 155 schemas and 2,591 root properties before nested shapes; four catalog attempts were inconsistent and non-machine-executable. AK evidence `5492` records that result.

The useful host observation is smaller: the host can prove, within one process and attempt, that it assigned and read back a prompt chain containing one exact component contribution, received and validated the exact registered acknowledgement callback's successful return through a private capability, and committed an insertion record before dispatch became eligible.

Decision 85 froze and reviewed:

- commit `14104636081ce127e46d56050ff3d07447c702ad`;
- tree `0893e65d2095f386f422c4de6fa0bc739ddb8ec7`;
- five-file aggregate `272c892af593ff10ddb056b1914f20372308fe8a47ca28b3ca04ca8e27882991`;
- vector accepted-object aggregate `e1a715cd868bdd9807eecb798b29ac02342697cc2afd9ac8eb7d9b6296b97a7e`.

Five strict lanes returned `ready_for_adr` with zero blockers and zero unresolved material findings. The controlling record is `docs/project/semantic-pi-insertion-evidence-v1-review-synthesis-r1.md`.

## Decision

Accept `semantic-pi-insertion-evidence-v1-r1` as the active successor direction for the Pi seam.

The protocol:

1. fixes identity to repository `pi-extensions`, component `pi-ontology-workflows`, and package `@tryinget/pi-ontology-workflows`;
2. prohibits every `pi-adapter` alias or fallback;
3. defines six named top-level schemas, eight digest domains, sixteen exact protocol cases, and thirteen exact host fixtures;
4. requires prepare -> apply -> assign -> readback -> private witness -> exact registered acknowledgement -> in-memory record commit before dispatch eligibility;
5. binds immutable loader registration, generation, attempt, handler index, operation-derived byte span, one-use witness state, and a six-entrypoint guard/frame matrix;
6. treats optional persisted JSON as unauthenticated audit data only;
7. proves only prompt-chain insertion observed before dispatch eligibility.

It does not prove or authorize provider transmission, model invocation/input/influence, semantic correctness, semantic delivery, publication, adoption, activation, consumer consent, live acquisition, or production use.

Decision 53 v0 remains accepted immutable history, while the broad successor packet/resolver/production direction from Decisions 71, 80, 82, and 84 is retired as an active implementation direction. All five decisions, their ADRs, frozen bytes, failed tasks, evidence, and reviews remain immutable non-authorizing history. Failed tasks `4230`, `4250`, `4278`, and `4298` and their downstream tasks are not reopened or reused.

## Consequences

- ADR acceptance permits only fresh owner-scoped implementation planning. Candidate implementation and all installation/live activity require separate authorization; this ADR supplies none.
- Fresh Decision-85 plans must define owner-scoped tasks plus validation/rollout/rollback before any later candidate authorization.
- ROCS may own deterministic schemas/vectors; Pi host owns callback invocation/control, application, assignment/readback, private witness/gateway, guards, validation, and record linearization; `pi-ontology-workflows` owns its contribution preparation and acknowledgement callback behavior without host/provider/model/production authority.
- No generic resolver, registry, SQL ledger, recovery actor, seccomp/Wasm protocol, semantic-release overlay, consumer graph, or production authority enters insertion-evidence v1.
- Generation/attempt/frame/guard sets are process-local operational state, not governance authority or durable recovery state.
- Installation, reload execution, dogfood, provider/model use, publication, activation, live acquisition, and production remain separately unauthorized.

## Rollback and supersession

Before implementation, rollback is simply to perform no owner task and keep the feature absent/default-off. After any separately authorized future implementation, rollback restores insertion evidence to absent/default-off; exact mechanism and optional audit-data disposition belong to owner-approved rollout/rollback planning. Any expansion beyond insertion-only evidence, any public issuance claim, any durable recovery, or any provider/model assertion requires a new decision and ADR.

## Non-authorization

This ADR records architecture and permits planning only. It does not itself implement or install code, create or authorize a candidate, authorize reload/dogfood/provider/model use, supply owner facts, or permit publication, activation, live, or production behavior. Neither the private witness nor persisted JSON is independently authenticated public proof.
