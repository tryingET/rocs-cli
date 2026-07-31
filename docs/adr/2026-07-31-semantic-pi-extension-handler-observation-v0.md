---
summary: "Accepts extension-local pre-return handler observation with one bounded diagnostic slot and no Pi-host insertion claim."
read_when:
  - "Implementing or reviewing Decision 89 extension-local handler observation."
type: "adr"
status: "proposed"
decision_id: 89
---
# ADR — Extension-local prompt-chain handler observation v0

## Status

Proposed for Decision 89 after strict three-lane convergence. Acceptance requires independent ADR review and AK transition through the Decision-89 membrane.

## Context

Decision 85 accepted a Pi-host insertion-evidence direction. Its corrected package-independent schema/vector substrate completed, but the host candidate stopped without a commit after controlling review found unresolved dispatch, provenance, stale-context, rollback, and no-oracle failures. The shared Pi host remained unchanged. Decision 89 therefore asks for the smallest observation the existing `pi-ontology-workflows` callback can make without host work.

Decision 89 froze and reviewed:

- commit `0dc38375e60c39a1a4040c228907ed999347d013`;
- tree `14210c26461ae0b50d62f6178e1c003fb00df803`;
- four-file aggregate `7415690b19a9ce63a6f0e016680ca51fd9a0e45f1bbb2cb65b8777548144c7b2`;
- RFC revision `pi-ontology-workflows-handler-observation-v0-r3`.

Pi-component implementability, governance/security, and scope/debt lanes all returned `ready_for_adr` with zero blockers and zero unresolved material findings. The controlling record is `docs/project/semantic-pi-extension-handler-observation-v0-review-synthesis-r3.md`.

## Decision

Accept `pi-ontology-workflows-handler-observation-v0-r3` as the successor architecture for this seam.

The package may, under separately authorized future work:

1. keep its current single registered `before_agent_start` handler;
2. extract a pure producer from the enabled semantic-preflight branch;
3. accept an observation only when output is exactly input followed by the canonical contribution;
4. preserve existing disabled hints and non-append framing replacement without a positive record;
5. construct the exact callback return object and assign one immutable record to one replaceable package-local diagnostic slot as the final package operation before the source-level return statement;
6. clear that slot on failure, non-append results, lifecycle/grant invalidation, disable, or replacement;
7. reuse existing generation/grant/cwd/compatibility checks without adding a host API, second host-ordered handler, observation lineage, queue, history, persistence, or unbounded retention.

An accepted local record proves only exact package-local append and return-value preparation. It does not prove execution of the return statement, callback return or promise settlement, host acceptance/assignment/readback, final-chain retention, provider transmission, model invocation/input/influence, public authenticity, semantic correctness, adoption, publication, activation, live acquisition, or production use. Compatibility tokens and self-produced digests remain non-authoritative.

## Consequences

- The fixed identity is repository `pi-extensions`, component `pi-ontology-workflows`, and package `@tryinget/pi-ontology-workflows`; no `pi-adapter` alias or host witness identity exists.
- `core/rocs-cli` owns immutable architecture history and reviewed claim wording. `pi-ontology-workflows` may own a later package implementation only under a fresh owner-scoped task.
- `pi-mono` owns no Decision-89 implementation change.
- ADR acceptance is necessary but not sufficient for implementation. Post-ADR implementation and validation/rollout/rollback planning must be attached through AK before any candidate work can become authoritative.
- Installation, reload, dogfood, provider/model use, publication, activation, live acquisition, and production each remain separately unauthorized.

## Decision-85 supersession obligation

Decision 85, its accepted ADR, completed R1b substrate, frozen artifacts, failed tasks, evidence, and reviews remain immutable history. Decision 89 supersedes only its active implementation direction.

ADR acceptance is not operational supersession by prose alone. Before Decision 89 can become unblocked or create an implementation task, the decision owner must record the successor disposition through AK. Decision-85 links for failed roots `4331` and `4343` plus pending executable graphs `4332` through `4339` and `4344` through `4350` must receive reevaluation status `cancelled` with notes naming Decision 89; task rows and historical artifacts remain intact. The Decision-85 passport must no longer present an unblocked executable direction or a still-valid pending continuation from either stopped graph.

## Rollback

Before implementation, rollback is to create no owner task and keep observation absent/default-off. Any separately authorized future implementation must define package-local rollback that clears the diagnostic slot and restores observation to absent while preserving existing semantic-preflight behavior. Any expansion to host evidence, callback settlement, durable history, provider/model claims, or production authority requires a new decision and ADR.

## Non-authorization

This ADR records architecture only. It does not implement or test code, authorize a candidate, install or reload Pi, run dogfood, permit provider/model use, publish or activate anything, or grant live/production authority.
