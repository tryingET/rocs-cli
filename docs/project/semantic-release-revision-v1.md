---
summary: "Decision 53 RFC revision v1 mapping the first strict owner, ROCS, and governance review findings to the revised RFC and machine packet."
read_when:
  - "Reviewing whether the first decision:53 synthesis findings were addressed."
type: "revision_note"
status: "complete"
decision: "53"
rfc_revision: "semantic-release-revision-v1"
source_review_synthesis: "semantic-release-review-synthesis-v0"
---

# Decision 53 — Semantic Release Revision v1

## Revision identity and legal effect

This note maps the first strict review set to RFC revision `semantic-release-revision-v1` and `docs/project/semantic-release-v0/`. It records documentation revision only. It does not close review, accept an ADR, authorize implementation/publication/adoption/activation/defaults/fleet rollout, mutate ontology, or change AK state.

## Artifact packet

| Artifact | Role |
|---|---|
| `semantic-release-capsule-and-consumer-adoption-protocol-v0.md` | revised owner/governance architecture and decision membrane |
| `semantic-release-v0/protocol.schema.json` | one closed Draft 2020-12 schema with 19 top-level protocol object variants |
| `semantic-release-v0/invariants.md` | canonical JSON, digests, complete trees, authority, compatibility, transactions, evidence, rollback, retention |
| `semantic-release-v0/golden-fixtures.json` | 20 canonical object preimages, two raw preimages, representative publication-to-rollback chain |
| `semantic-release-v0/differential-fixtures.json` | 11 fail-closed counterexamples |
| `semantic-release-v0/generate_fixtures.py` | deterministic fixture regeneration, non-authoritative |
| `semantic-release-v0/validate_fixtures.py` | independent stdlib-only recomputation and structural/invariant checks |

## Controlling synthesis blocker map

| Synthesis P0 | Revision coverage |
|---|---|
| 1. Authority and trust | RFC §§3, 6, 9; invariants §§4, 7–8. External owner trust root, owner issuance, separate consumer acceptance/activation, and self-certification rejection are explicit. |
| 2. Identity | RFC §§4–5, 7; invariants §§2, 5. Coordinate is a closed object; source/payload/capsule/publication/tool domains are separate; namespace/version binding is permanent CAS state. |
| 3. Machine contract | `protocol.schema.json` contains every requested artifact and closed nested object; both fixture files and validator are present. |
| 4. Compatibility | RFC §8; invariants §6. Owner policy, exhaustive categories, conditions, SemVer effect, unknown fail-closed, overrides, deprecation/removal, and tombstones are normative. |
| 5. Publication/materialization | RFC §§7, 9.3; invariants §§5, 7. Complete trees, lock/journal/fsync, atomic pointer/head, recovery, idempotency, conflict handling, and durable markers are defined. |
| 6. Evidence truth | RFC §10; invariants §9. ROCS generation, Pi delivery, AK linkage, and optional empirical outcome are typed with fixed issuer claim scopes. |
| 7. Rollback | RFC §11; invariants §10. Semantic/runtime/no-prior/combined paths are independent, pre-materialized, journaled, and append-only. |
| 8. Rollout governance | RFC §§9.4, 13–14; invariants §8. Canary/default/startup/fleet are separate gates; one slice is evidence only; Decision 52 is development-only. |

## Lane A — semantic owner and publication

| Finding | Disposition and exact coverage |
|---|---|
| A1. Issuance authority undefined | Addressed by RFC §§3, 6.1 and invariants §4: namespace policy/set/predicate, exact candidate/source approval, and ROCS non-issuer boundary. Schema: `ownerApproval`, `approvalVote`. |
| A2. Coordinate grammar and uniqueness open | Addressed by RFC §4 and invariants §5: closed coordinate object/SemVer subset, no build metadata, permanent `(namespace, version)` binding, idempotent replay, `version_conflict`. Schema: `coordinate`, `ownerPublication`. |
| A3. Source and capsule identity conflated | Addressed by RFC §§4–5 and invariants §§2–3: distinct digest domains, complete source/material trees, clean committed revision, generated material, exact omissions, separate build/tool receipt. |
| A4. Compatibility policy not implementable | Addressed by RFC §8 and invariants §6: owner policy revision/digest, exhaustive categories, deterministic maximum effect, machine conditions, unknown fail-closed, SemVer, overrides, deprecation/removal, permanent tombstones/no reuse. |
| A5. Unsigned local trust circular | Addressed by RFC §6.2 and invariants §4: external owner-controlled root, root/ledger minimum pins, owner publication chain, bootstrap/rotation, anti-rollback, withdrawal/revocation, offline cache rule, threat limit. |
| A6. Publication and predecessor not atomic | Addressed by RFC §7 and invariants §5: one namespace ledger, exact immediate accepted predecessor, CAS linearization, journal/fsync/recovery, conflict/fork rejection, idempotency, append-only withdrawal/replay. |
| A7. Rollback readiness asserted | Addressed by RFC §11 and invariants §10: pre-materialized predecessor, no-prior disable rehearsal, independent recovery runtime, semantic/runtime independence, immutable success/failure/history receipts. |

## Lane B — ROCS protocol and receipts

| Finding | Disposition and exact coverage |
|---|---|
| B1. No normative machine contract | Addressed by the closed Draft 2020-12 schema, invariants §§1–2/11, golden and differential fixtures, and independent validator. Integer-only duplicate-free I-JSON, safe range, unknown-field rejection, ordering, limits, and precedence are explicit. |
| B2. Digest contracts undefined | Addressed by invariants §2 domain/omission table and fixture canonical preimages. Raw blob, source, payload, capsule, publication, tool-bound build, intent, materialization, evidence, rollback, audit, and error identities are separate. Timestamp is separately bound. |
| B3. Complete materialization unprovable | Addressed by invariants §3 and manifest schemas: NFC POSIX paths, kinds, lengths, domain-separated byte digests, modes, UTF-8 order/uniqueness, collision rejection, exact tree equality, unlisted/missing/special/link/archive rejection. |
| B4. Tool and semantic identity conflated | Addressed by RFC §§4, 5.2 and invariants §3.7: `toolIdentity` is absent from capsule and bound by build, intent, verification, activation, generation, and rollback artifacts. |
| B5. Adoption can self-certify | Addressed by RFC §9 and invariants §§4, 7: external publication trust, separate consumer acceptance, exact complete inputs, independent runtime, reports/policy, prior receipt/rollback target, verifier/limits, and issuer scope. Technical artifact renamed materialization/verification receipt. |
| B6. Publication/adoption transactions absent | Addressed by RFC §§7, 9.3 and invariants §§5, 7: private staging, full verification, fsync, atomic pointer/head, durable marker, lock/journal/recovery, replay/conflict behavior, no mutation without atomic support. |
| B7. Use receipts not replayable | Addressed by RFC §10 and invariants §9: separate ROCS/Pi/AK schemas bind request/result/effective execution, IDs/packs, prompt-run digest, issuer, and claim scope; interpretation/influence is denied. |
| B8. Rollback no executable protocol | Addressed by RFC §11 and invariants §10: closed request/receipt shapes for semantic/runtime/combined/no-prior paths, preconditions, independent controller, partial failures, append-only history, deterministic errors. |
| B9. Resource/failure behavior open | Addressed by RFC §12 and invariants §§1, 11 plus `errorEnvelope`: fixed caps/deadline/no-network and mappings for trust absence, unknown/incompatible policy, drift, conflicts, recovery, rollback unavailability, and malformed input. |

## Lane C — governance and consumer adoption

| Finding | Disposition and exact coverage |
|---|---|
| C1. Consumer intent can self-certify consent | Addressed by RFC §§9.1–9.2 and invariants §§7–8: stable owner/repository/intent revisions, digest-bound accepted decisions/outcomes/scope, consumer acceptance authority, monotonic activation-epoch expiry/revocation, and external trust reference. |
| C2. Verification is not adoption authority | Addressed by RFC §§9.2–9.4: separate `ownerAcceptance`, `materializationVerificationReceipt`, and `activationReceipt`; ROCS receipt expressly denies consent/activation meaning. |
| C3. Canary/default/fleet gates conflated | Addressed by RFC §9.4 and invariants §8: intent, materialization, named canary, search, preflight, startup, and fleet are separate owner/AK gates. One vertical slice authorizes nothing. |
| C4. Use receipts overclaim exposure/influence | Addressed by RFC §10 and invariants §9: ROCS generation, Pi delivery/prompt-run binding, AK linkage, and optional DSPx/Oracle reference are distinct with bounded claims; session logs remain noncanonical. |
| C5. Rollback independence/history incomplete | Addressed by RFC §§11–12 and invariants §10: N→N−1 with fixed runtime, runtime rollback with N/revalidation, no-prior disable, combined partial recovery, pre-materialized targets, outside-root append-only history/GC. |
| C6. Decision 52/53 membrane weak | Addressed by RFC §13 and invariants §8: Decision 52 is development-only; Decision 53 needs fresh closure, ADR, two plans, fan-out/tasks, reevaluation, and AK unblocked before implementation; later gates remain separate. |
| C7. Cross-repo rollout ownership absent | Addressed by RFC §14 candidate fan-out naming semantic owner, ROCS, AK/consumer, Pi, and empirical lanes with consent, evidence, rollback owner, and stop conditions; explicitly not authorized. |

## Lane C P1 controls

| Finding | Disposition |
|---|---|
| Explicit RFC revision identity | Front matter and fixture metadata use `semantic-release-revision-v1`; this note binds the review mapping. |
| Missing/stale/revoked/inaccessible references | RFC §§6.2, 9.2, 12 and invariants §§4, 8, 11 fail closed with typed errors; stale/revoked fixtures are included. |
| Rename/fork/fleet repository identity | RFC §9.1 and invariants §7.3 define stable repository ID, owner-issued locator revision, new fork identity, and per-repository fleet aggregation. |

## Required invalid fixture coverage

| Required counterexample | Differential case(s) |
|---|---|
| self-certification | `consumer_cannot_self_certify_acceptance` |
| version conflict | `namespace_version_digest_reuse_conflicts` |
| incomplete tree | `complete_tree_digest_mismatch` plus unsorted manifest case |
| compatibility unknown | `compatibility_unknown_fails_closed` |
| mutable timestamp | `timestamp_forbidden_in_receipt` |
| stale/revoked trust | two stale revision cases and `trust_root_explicitly_revoked` |
| rollback unavailability | `semantic_rollback_target_not_materialized` |

## Validation record

Run from repository root:

```text
$ python3 docs/project/semantic-release-v0/generate_fixtures.py
wrote 20 golden records and 11 differential cases

$ python3 docs/project/semantic-release-v0/validate_fixtures.py
schema: Draft 2020-12 marker, closed objects, and 19 protocol types verified
golden: 20 canonical object preimages and 2 raw preimages recomputed
chain: 18 digest links verified
differential: 11 counterexamples rejected with expected errors
result: PASS (stdlib-only independent validator)
```

Fresh strict review, not this note, determines whether the revised packet is sufficient for later ADR consideration.
