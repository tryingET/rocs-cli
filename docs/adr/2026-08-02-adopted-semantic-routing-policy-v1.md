---
summary: "Decision 103 accepts exact adopted semantic-routing policy packet r14; only a corrected implementation plan and then separately scoped synthetic P1 are authorized."
read_when:
  - "Implementing or reviewing Decision 103."
  - "Planning any real semantic-routing policy, publication, consumer shadow, or automatic preflight."
type: "adr"
status: "accepted"
decision_id: 103
---
# ADR — Adopted semantic-routing policy v1

- Status: Accepted; supersedes the r11 Decision 103 ADR in this path
- Date: 2026-08-02
- Decision: 103

## Superseded and rejected revisions

The former r5-bound draft in this path remains rejected by executability review `dispatch-1785629031503` for a digest cycle and impossible phase timing. Its commits and rejection marker remain non-authorizing Git history. Nothing in this ADR rehabilitates r5.

The r11 Decision 103 ADR previously recorded in this path is superseded. Implementation work against r11 exposed two constructibility defects: an inventory self-hash, caused by equating the candidate and nested-inventory Git coordinates, and a P3→P4 phase defect, caused by making P3 readiness depend on inventory authority/preimage bytes not constructible until P4. The r11 packet, review closure, ADR authorization, and work based on them are therefore retired and non-authorizing. Revisions r12 and r13 were corrective review iterations, not accepted substitutes. This ADR supersedes r11 only after exact r14 received fresh unanimous strict convergence.

## Context

Decision 102 implemented and dogfooded a deterministic abstaining semantic router with conspicuously synthetic policy. It proved development mechanics, not ontology-owner approval, real-policy quality, publication currentness, consumer adoption, Pi/runtime integration, provider/model delivery, or production readiness.

Decision 98 B0 remains a frozen failed experiment. Its prompts, corpus, labels, evaluator, scenarios, templates, aliases, scores, floors, and outputs are permanently prohibited as future policy, D/U/O, evaluator, fixtures, regression inputs, or execution material.

Decision 103 strict review accepted only this exact normative r14 packet:

- packet commit `0782c4421bbab446c0aa8d6d5ff2f784fcdb81c9`;
- packet tree `18b7607c65181a416294af16a9879d5b3b097e31`;
- packet aggregate SHA-256 `b3c4c60b8a98d5e739498547c8e65b8613a9ce446c1fa4fa252d58fd4169fb98`;
- packet-manifest SHA-256 `5cee262377d7670834b771006fb1482df2d6dab833c928d400b427821700d7dc`.

The unanimous exact-r14 review lanes were:

- semantic authority and publication boundary: `dispatch-1785698793977` — accept;
- protocol/security and execution lifecycle: `dispatch-1785698793977-1` — accept;
- empirical custody and terminal access: `dispatch-1785698793978` — accept;
- constructibility, digest DAG, and phase ordering: `dispatch-1785698793979` — accept;
- controlling synthesis: `dispatch-1785699769802` — accept.

Any normative packet-byte change retires this closure and requires a new exact review, synthesis, and superseding ADR.

## Decision

Accept the exact r14 adopted semantic-routing policy v1 protocol and authority split defined by:

- `docs/project/semantic-router-adopted-policy-v1-rfc.md`;
- `docs/project/semantic-router-adopted-policy-v1/protocol.schema.json`;
- `docs/project/semantic-router-adopted-policy-v1/invariants.md`;
- `docs/project/semantic-router-adopted-policy-v1-validation-rollout-rollback.md`;
- `docs/project/semantic-router-adopted-policy-v1/packet-manifest.json`.

The architecture shall:

1. use two distinct, constructible Git coordinates: P3 inventory coordinate **I** and strict-descendant P4 candidate coordinate **C**, with both the commit and tree pairs unequal;
2. require P3, before D disclosure, to bind and validate the complete inventory preimage from explicit local I repository and source-byte inputs: the full inventory object, authoritative source path, exact canonical source bytes and raw SHA-256 digest, fixed deterministic extractor, extracted IDs, ontology snapshot, I commit/tree, coordinate digest, and equal signed-subject and independent-caller-request object/digest values;
3. require P4 alone to create C after accepted P3 readiness, with I a strict ancestor of C, while retaining at C the byte-identical canonical inventory source at the same path and every exact policy, provenance, and named provenance-source byte required by the packet; candidate inventory/selectable IDs must equal the P3 extraction while candidate owner coordinates remain C and nested inventory owner coordinates remain I;
4. bound any future real policy to IDs actually emitted by that exact frozen `softwareco/ontology` inventory source, while keeping `core/ontology-kernel` as upstream meaning authority for core IDs without copying or relabelling ownership;
5. separate policy candidate, independent custody/verdict, semantic-owner publication, trusted acquisition/currentness, future consumer adoption, and runtime use;
6. require fresh D/U/O custody, exact role separation, contamination controls, and one immutable evaluation attempt with two preregistered internal passes;
7. preserve the executable acyclic order from P3 custody readiness through P7 publication, including channel → challenge → unsigned start subject → caller request → evaluator signature;
8. authenticate the actual evaluator and custodian gateway, consume one reservation before spawn, prove timely custodian-observed spawn, allow only gateway-mediated revocable protected handles, and require process reaping, handle closure, and terminal revoke before verdict;
9. bind candidate, policy/provenance, inventory, custody, contamination, preregistration, execution, approvals, publication history, owner checkpoints, currentness, and verification through closed canonical digest/equality schedules;
10. require externally pinned authority credentials, keys, signatures, acquisition channels, single-use challenge consumption, clocks, and monotonic checkpoints before any production-currentness claim;
11. keep publication, withdrawal, and revocation with the Softwareco ontology owner; deterministic verification with ROCS; empirical custody/verdict with a separately accepted custodian; lineage with AK; and any future adoption/rollback with an exact consumer owner;
12. fail closed on missing, stale, forked, replayed, withdrawn, revoked, unauthorized, contaminated, exposed, malformed, over-budget, indeterminate, unreaped, unclosed, self-hashed, phase-invalid, preimage-missing, or coordinate-equal evidence.

ROCS verifies protocol objects; it does not issue semantic-owner, custodian, consumer, Pi/runtime, provider/model, or automatic-preflight authority.

## Authorized next work

This ADR authorizes only:

1. creation and independent review of a corrected implementation plan over the exact r14 coordinates above; then
2. only after that plan is accepted, a separately scoped owner task for synthetic P1: the bounded offline ROCS verifier and synthetic fixtures specified by r14.

The plan is not implementation authority. Plan acceptance does not itself start P1: P1 requires its own exact owner-scoped task, allowed and forbidden paths, predecessor identity, independent review, deterministic validation evidence, and rollback proof. P1 completion does not authorize P2 or any later phase. Any move beyond synthetic P1 requires a later explicit decision and task.

## Explicitly not authorized

- implementation before acceptance of the corrected implementation plan or outside the separately scoped synthetic P1 task;
- P2-P7 work, including storage mechanics, live policy authoring or execution, and any real custody, creation, disclosure, access, sealing, or use of D/U/O;
- publication, withdrawal, revocation, owner acquisition/currentness, live key provisioning, or any other live semantic-owner effect;
- consumer adoption or shadowing, Pi/runtime integration, prompt projection, provider/model invocation, or behavioral-benefit claims;
- automatic preflight, startup/default behavior, a second consumer, or fleet rollout;
- authoring or exposing raw U/O outside a future separately accepted custodian;
- rerunning, tuning, relabelling, or reusing Decision 98 B0;
- treating Decision 102 development evidence as owner adoption or production evidence;
- substituting Decision 53's unresolved canary, Pi-adapter, or recovery-controller identities;
- using local files, packet commits, AK records, intercom, session logs, this ADR, the implementation plan, or synthetic P1 output as owner-issued live authority.

## Consequences

### Positive

- P3 inventory authority is fully preimage-bound and constructible before D disclosure.
- The unequal I/C model removes the inventory self-hash and P3→P4 timing defects while proving strict ancestry and byte retention.
- Real routing authority can be represented without allowing ROCS, AK, a custodian, Pi, or a consumer to self-issue semantic approval.
- Publication and action-time currentness remain distinct; old valid bytes cannot substitute for a fresh authenticated owner-state read.

### Costs

- The protocol is intentionally large because meaning authority, custody, cryptography, process lifecycle, publication, currentness, and rollback remain separate proof domains.
- Real evaluation requires independent principals, protected storage, sealed data, exact credentials/keys, and one-shot discipline.
- All live policy, D/U/O, publication, consumer, Pi, and preflight effects remain blocked.

## Validation

Authorized post-ADR planning and synthetic P1 work must preserve:

- the exact r14 packet coordinates and full I-bound inventory object/preimages;
- strict I→C ancestry, unequal commit/tree pairs, and byte-identical inventory/source retention;
- exact Python and independent-Node agreement for schema, canonical JSON, 61 digest domains, signature preimages, equality joins, and eight attempt/verdict branches;
- unchanged Decision 102 route and discovery behavior;
- bounded offline execution, explicit local inputs, safe errors, and no network or live authority effects;
- complete self-hash, phase-order, missing-preimage, replay, stale-head, fork, revocation, deadline, process/handle closure, resource, and rollback rejection matrices;
- immutable B0 exclusion and no real D/U/O access;
- stage-specific synthetic claims that never imply later evidence dimensions.

## Rollback and supersession

Rollback of planning or synthetic P1 disables the synthetic verifier invocation and preserves plans, fixtures, reports, reviews, and failed evidence. It performs no publication or live-state mutation because none is authorized.

A normative packet-byte change requires fresh strict convergence and a superseding ADR. A real policy, D/U/O operation, P2 or later phase, cross-owner or core-owned policy, different company, changed authority identity, live publication/currentness, consumer, Pi/runtime integration, prompt projection, or automatic preflight requires a later accepted decision. No later decision may erase the Decision 98 failure history, Decision 102's development-only status, the r5 rejection, or the r11 supersession recorded here.
