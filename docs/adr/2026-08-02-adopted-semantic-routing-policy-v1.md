---
summary: "Decision 103 accepts the exact r11 adopted semantic-routing policy protocol and authority split; implementation and live effects remain separately gated."
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

## Superseded rejected draft

The former r5-bound draft in this path was rejected by executability review `dispatch-1785629031503` for a digest cycle and impossible phase timing. Its commits and rejection marker remain non-authorizing Git history. This ADR replaces that draft only after corrected packet r11 received fresh strict convergence.

## Context

Decision 102 implemented and dogfooded a deterministic abstaining semantic router with conspicuously synthetic policy. It proved development mechanics, not ontology-owner approval, real-policy quality, publication currentness, consumer adoption, Pi/runtime integration, provider/model delivery, or production readiness.

Decision 98 B0 remains a frozen failed experiment. Its prompts, corpus, labels, evaluator, scenarios, templates, aliases, scores, floors, and outputs are permanently prohibited as future policy, D/U/O, evaluator, fixtures, regression inputs, or execution material.

Decision 103 strict review accepted only this exact normative packet:

- packet commit `94f2d273c5f2ce27959978b82a37a3b2a8088867`;
- packet tree `fb2588f0623d92b80b46fd4b0f937e346cd32f83`;
- packet aggregate `20e8df2547bb4816325c7546a3c0a43b0283c6e0589d123e71b809baa7bfe438`;
- packet-manifest SHA-256 `05b39534733a81a2eb806d9c183033d7a0396e11d93c68f6a5f613fb80448fc5`;
- controlling synthesis commit `2295ba63368e9de9aff68779ead033e3cc51b405`.

Final review concerns:

- semantic authority and publication boundary: `dispatch-1785648963446` — accept;
- protocol/security and execution lifecycle: `dispatch-1785647681550` — accept;
- empirical custody and terminal access: `dispatch-1785647681551` — accept;
- constructibility, digest DAG, and phase ordering: `dispatch-1785647681552` — accept;
- controlling synthesis accuracy: `dispatch-1785649242877` — accept.

Any normative packet-byte change retires that closure and requires a new exact review and synthesis before this ADR can authorize work against the changed packet.

## Decision

Accept the exact r11 adopted semantic-routing policy v1 protocol and authority split defined by:

- `docs/project/semantic-router-adopted-policy-v1-rfc.md`;
- `docs/project/semantic-router-adopted-policy-v1/protocol.schema.json`;
- `docs/project/semantic-router-adopted-policy-v1/invariants.md`;
- `docs/project/semantic-router-adopted-policy-v1-validation-rollout-rollback.md`;
- `docs/project/semantic-router-adopted-policy-v1/packet-manifest.json`.

The architecture shall:

1. bound the first real policy to IDs actually owned by the frozen `softwareco/ontology` inventory;
2. keep `core/ontology-kernel` as upstream meaning authority for core IDs without copying or relabelling ownership;
3. separate policy candidate, independent custody/verdict, semantic-owner publication, trusted acquisition/currentness, future consumer adoption, and runtime use;
4. require fresh D/U/O custody, exact role separation, contamination controls, and one immutable evaluation attempt with two preregistered internal passes;
5. preserve the executable acyclic order from P3 custody readiness through P7 publication, including channel → challenge → unsigned start subject → caller request → evaluator signature;
6. authenticate the actual evaluator and custodian gateway, consume one reservation before spawn, prove timely custodian-observed spawn, allow only gateway-mediated revocable protected handles, and require process reaping, handle closure, and terminal revoke before verdict;
7. bind candidate, policy/provenance, inventory, custody, contamination, preregistration, execution, approvals, publication history, owner checkpoints, currentness, and verification through closed canonical digest/equality schedules;
8. require externally pinned authority credentials, keys, signatures, acquisition channels, single-use challenge consumption, clocks, and monotonic checkpoints before a production-currentness claim;
9. keep publication, withdrawal, and revocation with the Softwareco ontology owner; deterministic verification with ROCS; empirical custody/verdict with a separately accepted custodian; lineage with AK; and future adoption/rollback with an exact consumer owner;
10. fail closed on missing, stale, forked, replayed, withdrawn, revoked, unauthorized, contaminated, exposed, malformed, over-budget, indeterminate, unreaped, or unclosed evidence.

ROCS verifies protocol objects; it does not issue semantic-owner, custodian, consumer, Pi/runtime, provider/model, or automatic-preflight authority.

## Authorized next work

This ADR authorizes only creation and independent review of an implementation plan over the exact packet. After that plan is accepted, work may proceed only through separately scoped owner tasks in predecessor order:

```text
P1 ROCS offline verifier with synthetic fixtures
→ P2 synthetic Softwareco-owner storage mechanics
→ P3 fresh custody readiness and sealed D/U/O coordinates
→ P4 visible-D policy authoring and candidate freeze
→ P5 one-shot reservation/preregistration/activation
→ P6 one immutable protected evaluation and independent verdict
→ P7 semantic-owner publication only
→ later separately reviewed trusted acquisition/currentness implementation and live proof
→ later exact-consumer shadow decision
→ later prompt-projection canary
→ automatic preflight last
```

Passing one phase does not authorize the next. Each phase requires an owner-scoped AK task, exact predecessor identity, allowed/forbidden paths, independent review, validation evidence, and rollback proof.

## Explicitly not authorized

- implementation before an accepted implementation plan and P1 task;
- real policy execution before P1-P5 predecessor gates are accepted;
- authoring or exposing raw U/O outside its accepted custodian;
- rerunning, tuning, relabelling, or reusing Decision 98 B0;
- treating Decision 102 development evidence as owner adoption or production evidence;
- live owner acquisition, production currentness, live key provisioning, or owner publication before their exact owner gates;
- consumer shadowing, Pi/runtime integration, prompt projection, provider/model invocation, or behavioral-benefit claims;
- automatic preflight, startup/default behavior, a second consumer, or fleet rollout;
- substituting Decision 53's unresolved canary, Pi-adapter, or recovery-controller identities;
- using local files, packet commits, AK records, intercom, or session logs as owner-issued live authority.

## Consequences

### Positive

- Real routing authority can be represented without allowing ROCS, AK, a custodian, Pi, or a consumer to self-issue semantic approval.
- Offline evaluation is fresh, independently custodied, contamination-aware, one-shot, and falsifiable.
- Evaluator access is proof-of-possession bound, deadline bounded, gateway mediated, revocable, and terminally closed.
- Publication and action-time currentness remain distinct; old valid bytes cannot substitute for a fresh authenticated owner-state read.
- Withdrawal, revocation, abstention, operational error, and indeterminate evidence remain distinct and auditable.

### Costs

- The protocol is intentionally large because meaning authority, custody, cryptography, process lifecycle, publication, currentness, and rollback remain separate proof domains.
- Real evaluation requires independent principals, protected storage, sealed data, exact credentials/keys, and one-shot discipline.
- Live acquisition and consumer/runtime activation remain blocked until separately implemented and reviewed.

## Validation

Post-ADR work must preserve:

- exact Python and independent-Node agreement for schema, canonical JSON, 61 digest domains, signature preimages, equality joins, and eight attempt/verdict branches;
- unchanged Decision 102 route and discovery behavior;
- bounded offline execution and safe errors;
- complete replay, stale-head, fork, revocation, deadline, process/handle closure, resource, and rollback matrices;
- immutable B0 exclusion and protected U/O custody;
- stage-specific dogfood claims that never imply later evidence dimensions.

## Rollback and supersession

Before publication, rollback disables verifier/owner invocations and preserves candidates, reports, reviews, and failed evidence. Publication rollback is append-only withdrawal or revocation. A future consumer must own a separately current prior coordinate or disable target and use an independently rehearsed recovery path.

A normative packet-byte change requires fresh strict convergence and a superseding ADR. A cross-owner policy, core-owned policy, different company, changed authority identities, live consumer, prompt projection, or automatic-preflight default requires a later accepted decision and may supersede only the relevant boundary—not Decision 98 failure history or Decision 102 development evidence.
