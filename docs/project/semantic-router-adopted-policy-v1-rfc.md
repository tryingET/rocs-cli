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

`semantic-routing-policy-candidate.v1` binds exact owner commit/tree, policy and provenance paths/digests, Decision 102 protocol/algorithm coordinates, ontology snapshot, selectable Softwareco IDs, contamination manifest, and candidate digest.

### Verdict

`semantic-routing-policy-verdict.v1` binds the candidate to a preregistered evaluator and D/U/O coordinate, execution/metrics receipts, exact custodian and independent-review repository coordinates, approval-artifact digests, and `pass | fail | indeterminate` outcome. Only `pass` is publishable.

### Publication event and owner head

`semantic-routing-policy-publication-event.v1` is an append-only `publish | withdraw | revoke` event. Events form one sequence-checked hash chain inside one canonical `semantic-routing-policy-publication-history.v1` JCS object whose digest has a separate domain. `semantic-routing-policy-owner-head.v1` names that complete history's terminal event and exact owner repository/history identity observed through compare-and-swap publication.

A mutable filename such as `latest` has no authority. Current authorization requires the complete valid history object and terminal owner head.

### Currentness proof

`semantic-routing-policy-currentness-proof.v1` nests the candidate, pass verdict, complete publication history, owner head, and bounded local read receipt. The receipt binds a caller-pinned acquisition-capability coordinate, trusted approval digest, stable capture, and UTC capture completion. ROCS verifies that the terminal action is `publish`, all identities agree, and no later withdrawal/revocation exists.

The proof's `observed_at` must equal the receipt's immutable `capture_finished_at`; it cannot be re-dated independently. The caller separately pins both the acquisition-capability coordinate and the clock-source ID/approval digest plus maximum accepted uncertainty. Proof age is measured from that UTC instant against the verifier's trusted current clock and a caller-declared maximum of at most 300 seconds. Clock rollback, identity mismatch, or excess uncertainty fails closed. A future consumer must obtain the fresh receipt immediately before a separately authorized action.

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

The semantic owner freezes the eligible ontology snapshot and concept inventory first. A B0-unexposed DSPx/custodian then creates and seals U/O before D disclosure. Separate authors create D. Policy authors see only ontology meaning and D. U/O authors, annotators, adjudicator, and custodian remain independent of policy authors and implementers.

Raw U/O material remains in a private custodian-owned store and never enters ROCS, ontology Git history, Pi repositories, session summaries, or AK. AK may retain digests, custody receipts, aggregate verdict, and review references only.

### B0 prohibition

Decision 98 B0 prompts, labels, corpus, evaluator, outputs, rows, scenarios, templates, aliases, scores, and acceptance coordinates are prohibited as policy, D/U/O, regression, floor, or release sources. B0 exposure is recorded for every participant. Exposure retires a blind role or affected set.

### One-shot result

U/O executes once after candidate, evaluator, datasets, floors, identities, and rollback are preregistered. Outcome precedence is indeterminate first, valid fail second, pass last. No same-task repair or retry follows an observed fail or indeterminate effect.

The detailed floors and anti-overlap procedure remain those frozen in `semantic-router-v0-validation-rollout-rollback.md` unless a reviewed pre-data revision replaces them before any U/O author sees D or policy output. Floors never change after U/O observation.

## Owner publication process

A later ontology-owner implementation task must first accept exact root-relative candidate and publication-log paths, append-only/CAS storage mechanics, and rollback. A later policy-authoring task freezes one candidate. A separate empirical task returns only a verdict coordinate. Only then may an owner publication task append a `publish` event.

Withdrawal appends `withdraw`; integrity or unsafe-semantics invalidation appends `revoke`. Neither rewrites candidate, verdict, events, or consumer evidence. Republish after withdrawal uses a new event; a revoked candidate can never be republished.

## ROCS implementation boundary

A post-ADR ROCS task may implement only offline parsing, canonicalization, all seven digest domains, complete-history/currentness validation, safe errors, independent Node fixtures, and a no-live-acquisition CLI verifier over explicit local files. It must keep `live_acquisition_implemented=false` until an owner-specific capability is separately reviewed.

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
