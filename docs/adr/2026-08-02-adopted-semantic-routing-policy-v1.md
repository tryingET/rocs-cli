---
summary: "Accept an owner-issued Softwareco semantic-routing policy coordinate, independent offline acceptance contract, and authenticated action-time currentness proof."
read_when:
  - "Implementing or reviewing Decision 103."
  - "Planning any real semantic-routing policy, publication, consumer shadow, or automatic preflight."
type: "adr"
status: "accepted"
decision_id: 103
---
# ADR — Adopted semantic-routing policy v1

- Status: Accepted
- Date: 2026-08-02
- Decision: 103

## Context

Decision 102 implemented and dogfooded a deterministic abstaining semantic router using conspicuously synthetic policy only. It proved development mechanics, not ontology-owner approval, real-policy quality, publication currentness, consumer adoption, Pi integration, provider/model delivery, or production readiness.

Decision 98 B0 remains a frozen failed experiment. Its null-rejection failure established that retrieval is not admission, but its prompts, corpus, labels, evaluator, scenarios, scores, floors, and outputs are permanently prohibited as future policy or evaluation material.

Decision 103's strict review converged on this exact packet:

- packet commit `415e73d2f4128041911a76414a4d407ad20e0c31`;
- packet tree `01b6200b1ef6533b84dd93df81f385e4d8454f15`;
- packet aggregate `198b0203511650abd72f33962096f9b5004932de5163804849b60a057c814f0b`;
- packet-manifest SHA-256 `22beb1a62e625e02ef1b98da62b871782b8585c4cc47a1faf45feeb2805981df`;
- controlling synthesis commit `5f15fee7fe411738d97778dfc708443b638ee3ad`.

Final review lanes:

- semantic authority: `dispatch-1785623427853` — accept;
- protocol/security: `dispatch-1785623427853-1` — accept;
- empirical custody: `dispatch-1785623427854` — accept;
- synthesis review: `dispatch-1785628643305` — accept.

## Decision

Accept the adopted semantic-routing policy v1 protocol and authority split defined by:

- `docs/project/semantic-router-adopted-policy-v1-rfc.md`;
- `docs/project/semantic-router-adopted-policy-v1/protocol.schema.json`;
- `docs/project/semantic-router-adopted-policy-v1/invariants.md`;
- `docs/project/semantic-router-adopted-policy-v1-validation-rollout-rollback.md`.

The accepted architecture shall:

1. bound the first real policy to IDs actually owned by the frozen `softwareco/ontology` inventory;
2. keep `core/ontology-kernel` as upstream meaning authority for core IDs without copying or relabeling that ownership;
3. separate policy candidate, independent verdict, semantic-owner publication, future consumer adoption, and runtime use;
4. require fresh D/U/O custody, exact role separation, contamination controls, and one immutable evaluation attempt with two preregistered internal passes;
5. bind candidate, policy/provenance, inventory, custody, contamination, preregistration, execution, approvals, publication history, owner checkpoints, currentness, and verification through closed canonical digest/equality schedules;
6. require authenticated externally pinned authority credentials, signatures, acquisition channels, challenge-consumption storage, clocks, and action-time currentness;
7. keep publication, withdrawal, and revocation with the Softwareco ontology owner; deterministic verification with ROCS; empirical custody/verdict with a separately accepted custodian; AK lineage with AK; and future adoption/rollback with an exact consumer owner;
8. fail closed on missing, stale, forked, replayed, withdrawn, revoked, unauthorized, contaminated, exposed, malformed, over-budget, or indeterminate evidence.

## Authorized next work

After a separately reviewed implementation plan, Decision 103 may authorize staged work only in predecessor order:

```text
P1 ROCS offline verifier with synthetic fixtures
→ P2 Softwareco-owner storage mechanics with synthetic data
→ P3 fresh custody and preregistration
→ P4 visible-D real policy authoring
→ P5 one-shot sealed U/O execution
→ P6 semantic-owner publication
```

Each phase requires owner-scoped AK tasks, exact paths, predecessor evidence, independent review, and rollback proof. Passing one phase does not authorize the next.

## Explicitly not authorized by this ADR

- executing a real policy before P1–P4 gates are accepted;
- authoring or exposing U/O outside its accepted custodian;
- rerunning, tuning, relabeling, or reusing Decision 98 B0;
- treating Decision 102 development results as owner adoption;
- live owner acquisition, live key provisioning, or publication before their owner gates;
- consumer shadowing, Pi integration, prompt projection, provider/model invocation, or behavioral-benefit claims;
- automatic preflight, startup/default behavior, a second consumer, or fleet rollout;
- substituting Decision 53's unresolved canary, Pi-adapter, or recovery-controller identities.

## Consequences

### Positive

- Real routing authority can be represented without allowing ROCS, AK, a custodian, Pi, or a consumer to self-issue semantic approval.
- Offline evaluation is fresh, independently custodied, contamination-aware, and falsifiable.
- Publication currentness is action-time authenticated state rather than a mutable filename or old valid digest.
- Withdrawal, revocation, abstention, and operational error remain distinct and auditable.

### Costs

- The protocol is intentionally large because authority, custody, signatures, currentness, and rollback remain separate proof domains.
- Real evaluation requires independent principals, protected storage, sealed data, and one-shot discipline.
- Live acquisition and consumer activation remain blocked until separately implemented and reviewed.

## Validation

Post-ADR work must preserve:

- exact Python/independent-Node schema, canonical JSON, digest, signature-preimage, and invariant agreement;
- unchanged Decision 102 route and discovery behavior;
- bounded offline execution and safe errors;
- complete replay, stale-head, fork, revocation, resource, and rollback matrices;
- immutable B0 exclusion and protected U/O custody;
- stage-specific dogfood claims that never imply later evidence dimensions.

## Rollback and supersession

Before publication, rollback disables verifier/owner invocations and preserves candidates, reports, reviews, and failed evidence. Publication rollback is append-only withdrawal or revocation. A future consumer must own a separately current prior-coordinate or disable target and use an independently rehearsed recovery path.

A cross-owner policy, core-owned policy, different company, changed authority identities, live consumer, prompt projection, or automatic-preflight default requires a later accepted decision and may supersede only the relevant boundary—not Decision 98 failure history or Decision 102 development evidence.
