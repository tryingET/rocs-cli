---
summary: "RFC for an owner-issued Softwareco routing-policy coordinate, offline acceptance verdict, and action-time currentness proof."
read_when:
  - "Reviewing Decision 103 or planning any non-synthetic semantic-route execution."
type: "rfc"
status: "proposed"
decision_id: 103
---
# RFC — Adopted semantic-routing policy v1

## Status

Proposed for Decision 103 strict multi-lane review. This packet authorizes no implementation, real policy, dataset, evaluation, publication, consumer integration, or runtime activation.

## Decision

Define a closed protocol that lets the Softwareco ontology owner freeze a routing-policy candidate, bind it to an independently custodied fresh offline pass verdict, publish/withdraw/revoke it through immutable owner history, and supply an action-time currentness proof that ROCS can verify without acquiring owner authority.

## Normative bundle

- [`semantic-router-adopted-policy-v1/protocol.schema.json`](semantic-router-adopted-policy-v1/protocol.schema.json);
- [`semantic-router-adopted-policy-v1/invariants.md`](semantic-router-adopted-policy-v1/invariants.md);
- this RFC.

The exact review packet is frozen by [`semantic-router-adopted-policy-v1/packet-manifest.json`](semantic-router-adopted-policy-v1/packet-manifest.json).

## First-policy boundary

The semantic owner is exactly `softwareco/ontology`. The first policy may select only Softwareco-owned ontology IDs. `core/ontology-kernel` remains an upstream ref layer and meaning owner for core IDs. The v1 policy cannot select core-owned IDs, copy core meaning into Softwareco provenance, span another company, or aggregate multiple publication owners.

Any such expansion requires a superseding architecture decision.

## State separation

```text
ontology meaning authored
→ policy candidate frozen
→ independent offline verdict fixed
→ semantic owner publishes
→ future consumer desires/adopts
→ future runtime uses
```

Each arrow is an explicit owner transition. Candidate, verdict, publication, currentness, adoption, and use receipts are non-interchangeable.

## Protocol objects

### Candidate

`semantic-routing-policy-candidate.v1` binds exact owner commit/tree, policy and provenance paths/digests, Decision 102 protocol/algorithm coordinates, ontology snapshot, exact frozen owner-inventory path/digest, selectable canonical `co.software.*` IDs proven members of that inventory, a candidate-contamination manifest covering exactly ten pre-attempt B0-deny surfaces, and candidate digest. The candidate manifest contains neither candidate nor attempt-envelope digest, so candidate identity is acyclic. A separate semantic-binding object and closed extractor receipt record the parsed Decision 102 policy owner, provenance manifest owner, every per-record `source_owner_repo`, all executable concept/joint-route IDs, nested canonical inventory object/digest, and verification receipt; every ID must belong to the frozen inventory. Prefix shape alone never proves ownership, and every later selected route ID remains bounded by the same set.

### Verdict

`semantic-routing-policy-verdict.v1` binds the candidate to nested closed custody-policy, candidate-contamination manifest, downstream execution-contamination attestation, post-candidate preregistration, attempt-envelope, and one-attempt objects; a preregistered evaluator and D/U/O coordinate; execution/metrics receipts; authenticated custodian and distinct independent-review principal coordinates; and `pass | fail | indeterminate` outcome. A non-circular verdict-approval subject binds every approval-relevant coordinate and the exact outcome while excluding the approvals and verdict digest. Custodian and reviewer each issue a separately signed approval over that subject under externally pinned authority credentials, trust roots, and canonical raw-32-byte Ed25519 public keys. Authority coordinates identify separate credential digests, never their enclosing approvals, preventing a subject/approval cycle. Repository strings, opaque references, or unsigned self-digests convey no authority. Only `pass` is publishable.

### Publication event and owner head

`semantic-routing-policy-publication-event.v1` is an append-only `publish | withdraw | revoke` event with a closed, authenticated owner approval artifact whose non-circular subject binds the exact owner authority, sequence, predecessor, action, candidate, verdict, reason, and time. The signed subject excludes approval and event digests, preventing both digest cycles and replay across changed events. Events form one sequence-checked hash chain inside one canonical `semantic-routing-policy-publication-history.v1` JCS object whose digest has a separate domain. `semantic-routing-policy-owner-head.v1` names that complete history's terminal event and exact owner repository/history identity under an authenticated monotonically increasing compare-and-swap owner checkpoint.

A mutable filename such as `latest` has no authority. Current authorization requires the complete valid history object, terminal owner head, and authenticated current owner-store checkpoint. Publish is capped at sequence 9,999 and must reserve byte/event capacity for a final sequence-10,000 withdrawal or revocation.

### Currentness proof

`semantic-routing-policy-currentness-proof.v1` nests the candidate, pass verdict, complete publication history, owner head, a contiguous authenticated checkpoint chain, fresh caller challenge, issuer-trust bundle, bounded local read receipt, issuer Ed25519 attestation, and authenticated single-use challenge-consumption receipt with a separately domain-digested signing body. The trust bundle contains closed domain-digested acquisition-channel, challenge-consumption-store, and consumption-signing-key coordinates plus a distinct consumption authority credential carrying the canonical raw 32-byte Ed25519 public key. Closed approval artifacts bind issuer, exact coordinate subject, purpose, validity, and revocation state. The receipt binds the caller-pinned acquisition capability, trusted clock/channel/store identities, challenge/action/candidate, monotonic checkpoint, stable capture, and issuer attestation. ROCS verifies every equality join and that the terminal action is `publish` under the authenticated current checkpoint.

The proof's `observed_at` must equal issuer-attested `capture_finished_at`; a digest recomputation cannot re-date it. The signed receipt body also covers descriptor-anchored no-follow capture plus the closed-environment, no-network, stable-final-recheck, and exact acquisition-channel-coordinate assertions, so those guarantees cannot be changed by wrapping an otherwise valid attestation in a recomputed receipt. The Ed25519 signature covers a separately domain-separated receipt body and approved key coordinate without a digest cycle. The consumption signature verifies only under the exact raw key bytes in the caller-pinned consumption credential; no ambient key registry or unpinned caller key is permitted. The caller supplies a separate `semantic-routing-policy-verification-request.v1` API input pinning trust/challenge/receipt-attestation/checkpoint digests, prior/minimum checkpoint, intended action, capability, the three complete channel/store/consumption-key coordinate objects and digests, the complete consumption credential and key bytes/digests, consumption receipt/issuer, trusted clock, age, uncertainty, and the exact custodian, independent-review, and semantic-owner authority coordinates plus their separate authority credentials, signed approval digests, trust roots, and canonical public-key bytes/digests. Values nested only in the proof are never caller authority. A challenge is single-use and expires. Proof age is at most 300 seconds. Replayed H1 fails once authoritative checkpoint H2 records withdrawal/revocation, even when old H1 bytes remain valid history. Currentness cannot pass until a later owner task implements this trusted acquisition boundary.

## Authority split

| Fact/action | Sole issuer or owner |
|---|---|
| Softwareco ontology meaning and selectable IDs | `softwareco/ontology` semantic owner |
| policy clauses, provenance, candidate approval | same semantic owner |
| U/O custody and frozen verdict | named independent DSPx/custodian |
| deterministic schema/digest/history/currentness verification | ROCS |
| decision/task/evidence linkage | AK |
| publication, withdrawal, revocation | semantic owner |
| adoption, suppression, activation, rollback | future exact consumer owner |
| delivery/runtime attestation | future Pi owner |
| recovery execution | future independent recovery owner |

ROCS does not publish. AK does not store policy or U/O bytes. DSPx does not define ontology meaning. A consumer cannot override abstention or currentness failure.

## Relationship to Decision 53

Decision 53 supplies precedent for immutable release state, owner-specific facts, currentness, consumer separation, and rollback. Its exact `pi-canary-consumer`, Pi adapter, canary, and recovery identities remain unresolved and are not imported or substituted here.

Decision 103 defines routing-policy publication and offline acceptance only. It neither activates Decision 53 live gates nor selects a consumer.

## Fresh evaluation contract

Decision 102's V1–V3 design is adopted as the required future evaluation shape, under new owner tasks:

- D: 360 visible development rows across 12 strata;
- U: 600 untouched acceptance rows, 300 applicable and 300 null/adversarial;
- O: 96 untouched operational rows across eight classes.

The semantic owner freezes the eligible ontology snapshot and exact `co.software.*` inventory first. Before any rows exist, DSPx issues a digest-bound custody policy covering exact source and license/consent authority coordinates, privacy class and the complete prohibited-content set, ACL/audit, retention, backups, all expiry/withdrawal/privacy-exposure deletion triggers, verified deletion, exposure retirement, and incident response. B0-unexposed U/O authors then create and seal U/O before D disclosure. Separate authors create D.

The execution sequence is acyclic and stage-bound. P3 fixes custody/roles, seals D/U/O before D disclosure, and emits a custodian-signed custody-readiness subject/receipt verified against a separate caller request; it contains no policy/provenance, candidate, preregistration, or execution field, and its base access history grants the evaluator operator no sealed-row read or process-start authority. P4 then discloses D, authors policy/provenance, freezes the ten-surface candidate-contamination manifest, and freezes the candidate. P5 first acquires a non-executing, expiring custodian reservation whose executor equals the frozen evaluator-operator assignment, then creates the candidate-and-reservation-bound attempt envelope and a custodian-and-independent-review-signed downstream execution-contamination subject/attestation verified against a separate caller request. A closed preexecution-verification bundle nests both complete caller-request preimages and their digests before preregistration closes; opaque digests are invalid. Only after every request, signature, preregistration, authority, reservation, and equality join validates may the custodian sign one protected-access activation. That activation binds the unchanged P3 base history (at most 254 events), exact evaluator operator, U/O seals, reservation, permissions, expiry, activated-history digest, and exact grant-event digest; the grant is time-equal to the signed issuance and leaves one event slot for mandatory closure. The reservation alone grants no sealed-row read or process-start authority and expires or is released unused on validation failure. The preregistration binds explicit custodian/reviewer authority coordinates byte-equal across role assignments, custody policy, P3/P5 signed subjects, credentials, approval issuers, caller-request preimages, plus the exact canonical role set and cardinalities (including implementer and two distinct annotators), twelve pairwise-distinct authenticated principals, append-only base access history, nested B0 exposure evidence, closed mutual-exclusion receipt, exact candidate, both contamination objects, evaluator/floors, and a nested inspectable one-attempt envelope with exact argv/environment/runtime/seals/pass order/reservation/rollback. Custodian and independent reviewer are distinct principals; policy authors cannot author/access U/O; annotators/adjudicator/evaluator roles remain separated as normative invariants.

Raw U/O material remains in a private custodian-owned store and never enters ROCS, ontology Git history, Pi repositories, session summaries, or AK. AK may retain digests, custody receipts, aggregate verdict, and review references only.

### B0 prohibition

Decision 98 B0 prompts, labels, corpus, evaluator, outputs, rows, scenarios, templates, aliases, scores, and acceptance coordinates are prohibited as policy, D/U/O, evaluator, fixtures, regression, floor, template, alias, or execution sources. A closed candidate-contamination manifest binds canonical B0 preregistration commit `286773ee6a88b9fd2276f8008898c57ff9a073b9`, the failure commit and lock/prompt/report digests plus an exact ordered ten-surface no-reuse bijection over policy, D/U/O, evaluator, fixtures, floors, templates, aliases, and regression inputs. After candidate and envelope freeze, a separately signed downstream execution-contamination subject/attestation binds the candidate, candidate manifest, evaluator, and attempt-envelope coordinate with `no_reuse`; custodian and independent reviewer both authenticate it and an independent caller request pins their authorities, credentials, approvals, trust roots, and keys before execution. Together they cover all eleven prohibited surfaces without a back edge. B0 exposure is recorded for every participant. Exposure retires a blind role or affected set.

### One-shot result

U/O executes in one immutable P6 attempt only after P5 preregisters the exact candidate, evaluator, datasets, floors, identities, caller-request preimages, envelope, and rollback and the custodian issues the validated downstream access activation. Activation is not a bearer token: a fresh caller challenge/request pins frozen evaluator and launch-gateway credentials plus a closed mutually authenticated channel/exporter coordinate. The evaluator signs a prospective start authorization; on that live channel the gateway recomputes the exporter and crash-safely signs reservation consumption `0 → 1` before spawn with descriptors closed. It atomically signs a separate first-descriptor-handoff receipt before U/O row access. A completed invocation requires the handoff and ordered `primary`/`immediate_repeat` passes; no-start and interrupted prefixes retain exactly the proof/launch/handoff/receipt facts that actually exist and remain indeterminate. After a raw receipt, or on pre-start failure/abort/expiry, the exact custodian-signed closure appends the terminal revoke; expiry disables access, and no verdict exists without the correctly nullable start/launch/receipt fields and closure. Any second invocation, process retry, selective rerun, extra pass, or same-candidate repair is forbidden. Outcome precedence is indeterminate first, valid fail second, pass last.

The detailed floors and anti-overlap procedure remain those frozen in `semantic-router-v0-validation-rollout-rollback.md` unless a reviewed pre-data revision replaces them before any U/O author sees D or policy output. Floors never change after U/O observation.

## Owner publication process

A later ontology-owner implementation task must first accept exact root-relative candidate and publication-log paths, append-only/CAS storage mechanics, and rollback. A later policy-authoring task freezes one candidate. A separate P5 task preregisters the exact frozen candidate and attempt. A P6 empirical task executes once, fixes metrics/outcome, and only then obtains custodian and independent-review signatures over the post-execution verdict-approval subject. Only a later P7 owner-publication task may append a `publish` event.

Withdrawal appends `withdraw`; integrity or unsafe-semantics invalidation appends `revoke`. Neither rewrites candidate, verdict, events, or consumer evidence. Republish after withdrawal uses a new event; a revoked candidate can never be republished.

## ROCS implementation boundary

A post-ADR ROCS task may implement only offline parsing, canonicalization, all sixty-one digest domains, explicit topological dependency validation, complete-history/currentness validation, safe errors, independent Node fixtures, and a no-live-acquisition CLI verifier over explicit local files. Fixtures must include forged/redated receipts, replayed old publish H1 after withdrawal H2, challenge/action mismatch, trust/approval mismatch, role/access-history collision, incomplete/duplicate/unjoined contamination coverage, candidate→contamination→envelope back edges or any digest cycle, mismatched downstream execution-contamination attestation, policy/provenance per-record owner or inventory impostors, envelope/reservation/rollback drift, activation/detached-proof bearer replay, wrong executor or gateway key/channel, impossible prospective timestamp, absent crash-safe reservation-consumption receipt, forged channel exporter, row read before descriptor handoff, no-start/interrupted prefix-shape failure, backdated grant, access-history capacity exhaustion, missing/late closure or terminal revoke, history fork, and capacity-reserve boundaries. It must keep `live_acquisition_implemented=false` until an owner-specific capability is separately reviewed.

No ROCS implementation task may create real policy, read U/O, publish an owner event, name a consumer, call Pi, invoke a provider/model, or enable automatic preflight.

## Consumer sequence after a valid publication

Only after an independently reviewed pass and current owner publication may later decisions proceed, one at a time:

1. exact consumer identity and consent;
2. no-injection shadow using a command-only or deterministic faux-provider harness;
3. shadow evidence and independent rollback rehearsal;
4. separate prompt-projection decision and one opt-in canary;
5. behavioral/provider evidence under explicit authorization;
6. automatic preflight decision last.

No stage is implied by the previous one. A normal Pi prompt may use an ambient provider even when the extension adds no request; claims must distinguish those facts.

## Rollback

Before any consumer exists, rollback means disabling verifier invocation and preserving all artifacts. Owner withdrawal/revocation is append-only. A future consumer rollback requires a separately current prior coordinate or disable target, plus a recovery controller outside semantic/runtime replacement roots. Automatic preflight is prohibited until that recovery path is independently rehearsed.

## Alternatives rejected

- treating a development v0 result as adopted;
- mutable `latest` policy;
- ROCS or AK self-publication;
- one object combining verdict, publication, adoption, and use;
- policy spanning core and Softwareco IDs under one inferred owner;
- B0 repair or reuse;
- U/O stored in Git or visible to policy authors;
- shadow observation presented as provider/model evidence;
- automatic preflight before owner publication, consumer consent, and rollback proof.
