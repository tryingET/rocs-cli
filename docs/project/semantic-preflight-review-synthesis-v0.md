---
summary: "Controlling attempt-1 review synthesis for decision:52, requiring revision before ADR."
read_when:
  - "Checking decision:52 attempt-1 legal review closure."
  - "Revising semantic discovery and Pi preflight RFCs."
type: "review_synthesis"
decision_id: 52
review_outcome: "revise_rfc"
---

# Review Synthesis — Semantic Discovery and Pi Preflight v0

## Review chain status

- Decision: `52`
- Review kind: Tier-1 multi-lane pre-ADR synthesis
- Closure mode: `multi_lane_requires_synthesis`
- Primary: `semantic-discovery-protocol-v0.md@71a7fdc1bfaaa89e266b123fd9ca5a02fca2144e`
- Companion: `semantic-preflight-adapter-v0.md@f4941909fc2a74128648155b23e078cde0a2c0b2`
- Review-set plan: `semantic-preflight-review-set-plan-v0.md@7033a04`
- Synthesis procedure: Prompt Vault `layer12-070-decision-rfc-review`
- Internal critique method: Prompt Vault `many-of-the-greats`

## Input review attempts

1. [ROCS determinism and protocol](semantic-preflight-review-lane-rocs-v0.md)
2. [Pi runtime security and lifecycle](semantic-preflight-review-lane-pi-v0.md)
3. [Authority, adoption, and rollout](semantic-preflight-review-lane-governance-v0.md)

All three lanes recommend `revise_rfc`. There is no dissent to resolve and no legal basis for ADR progression.

## Overall verdict

```text
review_outcome = revise_rfc
next_legal_move = revise_rfc
ADR_legal_now = no
```

The proposed stable-core/thin-adapter direction survives adversarial review. The reviewed contract does not: identity domains, pack lineage, algorithm details, host lifecycle, consent, production-owner dependencies, defaults, and rollback are still architecture-shaping.

## Consolidated must-fixes

### ROCS protocol

1. Split corpus snapshot, release coordinate, effective execution/request, document, pack, and result identities.
2. Specify canonical encoding and every digest domain.
3. Define a portable capture/revalidation procedure and supported platform/filesystem/runtime matrix.
4. Make exact-ID pack provenance verifiable against discovery or explicitly return and validate a fresh identity.
5. Freeze the complete lexical algorithm, Unicode posture, limits, error schema, JSON transport, protocol negotiation, environment, and filesystem effects.

### Pi adapter

6. Use immutable or immediately reverified absolute runner descriptors; close TOCTOU.
7. Treat markers only as unauthenticated framing.
8. Rename scope to prompt-run and define steering/follow-up behavior.
9. Choose timeout-only preflight or require a host-level cancellable signal; specify process-tree closure and all stream/render limits.
10. Require TUI mode plus fresh confirmation for development enablement; define machine-visible failure readback and host compatibility negotiation.

### Governance and rollout

11. Remove pre-ADR implementation authorization and relabel all phases as candidate post-ADR sequencing.
12. Reserve production release identity without pre-deciding its owner contract. Separate semantic release, ROCS tool trust, and consumer adoption.
13. Complete controlled-vocabulary preflight and lifecycle links.
14. Separate explicit-search, automatic-preflight, and startup-orientation defaults.
15. Define independent capsule and adapter/runtime rollback plus phase-specific evidence gates.
16. Require a concrete later AK decision dependency before production adoption/cutover work.

## Material improvements required by strict convergence

- Add metamorphic/differential conformance fixtures to the proposed protocol contract.
- Add a versioned startup-context coexistence event contract or explicitly defer it with an owner and gate.
- Add a phase matrix covering identity, runner, ranking owner, automatic behavior, task role, evidence, and rollback.
- Strengthen evidence references with immutable revisions and retained receipts.

## Questions the revision must answer

1. Is a production release capsule semantic-corpus identity only, or does it include executable trust?
2. What owner surface advertises discovery protocol compatibility?
3. What exact consistency guarantee can ROCS prove over ordinary filesystems?
4. Is Pi preflight timeout-only, or must Pi expose pre-agent cancellation?
5. What evidence authorizes an adopted canary, package default search cutover, automatic preflight default, and fleet rollout respectively?

These are architecture questions, not post-ADR implementation details.

## Legal next move

1. Attach this synthesis as the controlling attempt-1 closure with `revise_rfc`.
2. Keep decision `52` in review.
3. Revise both RFCs together and link them to this synthesis.
4. Commit new immutable revisions.
5. Declare and execute a fresh review set against those revisions.
6. Draft an ADR only if the latest controlling synthesis becomes `ready_for_adr` with strict convergence satisfied.

## Non-authorizations

This synthesis does not authorize ADR drafting, implementation tasks, implementation, release-capsule adoption, runtime trust selection, default enablement, fleet rollout, or mandatory enforcement.
