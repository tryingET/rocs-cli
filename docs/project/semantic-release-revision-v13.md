---
summary: "Decision:53 semantic-release conclusive corrected revision v13 packet and validation record."
read_when:
  - "Reviewing Decision:53 corrected revision v13 or its fresh-review closure."
type: "revision_note"
status: "proposed"
rfc_revision: "semantic-release-revision-v13"
review_posture: "fresh_review_required"
---
# Semantic Release Revision v13

## Objective and controlling review

This conclusive corrected packet retains the `semantic-release-revision-v13` identity and every existing path. It preserves the closure of the controlling [`semantic-release-rereview12-synthesis-v12.md`](semantic-release-rereview12-synthesis-v12.md) and [`semantic-release-rereview12-greats-adjudication-v12.md`](semantic-release-rereview12-greats-adjudication-v12.md), closes the later v13 findings, and remains an offline proposal packet for fresh strict review. Work was performed under the operator-supplied active task `3953` without Agent Kernel mutation.

## Original v13 blocker closure

| Rereview12 blocker | Revision-v13 closure | Direct evidence |
|---|---|---|
| Recovery accepted a caller-supplied expected action and publication transactions omitted the complete approval action. | `semantic-publication-transaction.v0` carries closed `approved_action` and `approved_action_digest`; recovery derives the operation action and has no caller-supplied expected action. | `publication_recovery_coherent_wrong_action_kind_rejected`; `publication_recovery_coherent_wrong_action_coordinate_rejected` |
| Recovery-start state treated post-CAS recovery as prior state. | Pre-linearization starts at prior and discards; post-linearization starts and remains at result without a second CAS. | `recovery_prelinearization_observed_start_must_be_prior`; `recovery_postlinearization_observed_start_must_be_result`; `recovery_postlinearization_forbids_second_cas` |
| Single-canary scope stopped before generation and Pi delivery. | Generation and every Pi outcome bind the exact consumer repository and v0 canary scope. | `generation_canary_scope_must_equal_activation`; `generation_second_canary_rejected`; all three `pi_*_canary_scope_drift_rejected` cases |
| Tombstone history could reset genesis and did not bind authorization to the resulting head. | An external semantic-owner genesis anchor is mandatory; each non-genesis authorization equals the resulting lifecycle head and exact added-entry origin. | `lifecycle_tombstone_genesis_anchor_mismatch_rejected`; `tombstone_history_coherent_genesis_reset_rejected`; `tombstone_history_coordinated_wrong_authorization_rejected` |
| The differential corpus violated the 16-MiB artifact limit and loaders lacked file/depth bounds. | A closed manifest authenticates three deterministic shards; both validators enforce no-follow stable reads, strict UTF-8/no BOM, depth 64, safe paths, exact inventory, and aggregate reconstruction. | `raw_nesting_depth_64_accepts`; `raw_nesting_depth_65_rejected`; shard inventory below |

## Later v13 closure retained

| Finding | Closure | Direct evidence |
|---|---|---|
| Tombstone deltas could replay an ID or reuse/no-op/roll back a lifecycle head. | Added IDs are globally new, cumulative cardinality is prior `+1`, and each resulting head is fresh. | `tombstone_history_replayed_added_id_rejected`; `tombstone_history_lifecycle_head_noop_rejected`; `tombstone_history_lifecycle_head_rollback_rejected` |
| Recovery lacked accepted idempotent `committed/linearized/none` re-entry. | Committed replay requires exact state/marker equality, null intent, no staging, and no mutation. | `recovery_committed_replay_is_idempotent` plus marker/mutation/intent negatives |
| Shard bytes were parsed before authentication and path/read was raceable. | Both loaders authenticate stable retained bytes before decode/parse. | Python `stable_bounded_json_read`; Node `stableBoundedJsonRead` |
| Generation and Pi checked issuer kind but not exact adapter ID. | ROCS is exactly `rocs-cli`; Pi is exactly `pi-adapter`. | `generation_issuer_id_must_match_pinned_rocs_adapter`; `pi_issuer_id_must_match_pinned_delivery_adapter` |
| `ak_optional_pi` was shape-only. | It resolves exact AK task/decision/evidence lineage, activation, generation, and explicit optional Pi state. | Both accepted AK variants and direct task/decision/evidence/activation/generation/Pi negatives |

## Conclusive corrected-v13 closure

| Finding | Closure | Direct evidence |
|---|---|---|
| Cross-repository task receipts incorrectly treated ROCS, semantic, and consumer surfaces as canonical task authorities. | Agent Kernel is the sole task-state authority. Every resolved task uses `canonical_task_state:ak:<stable-task-id>`, category `ak_task`, and AK issuer/repository/store metadata. The embedded fact retains its exact AK/ROCS/semantic/consumer target repository, while its `ak_store_head` equals the enclosing AK receipt/pin. | Four accepted target-repository witnesses; `resolved_rocs_reference_non_ak_issuer_rejected`; `resolved_semantic_reference_non_ak_issuer_rejected`; `resolved_consumer_reference_non_ak_issuer_rejected` |
| A current-decision digest could arrive on a stale independent receipt. | Universal preflight requires current-decision receipt repository, store ID/locator/head/revision/revocation head, and action epoch to equal the canonical-store receipt; every typed decision carries the same complete store head. | `stale_independent_decision_receipt_rejected`; existing typed-decision store-drift negatives |
| Aggregate limits were enforced only after all shard reads. | Before any shard open, retained schema/golden/manifest lengths plus all listed shard lengths and shard count are checked. Shards are then read incrementally, and cumulative actual retained lengths are checked after each acquisition before parse. | `transport_manifest_listed_bytes_overflow_rejected_before_shard_reads`; `transport_actual_retained_bytes_overflow_rejected_during_acquisition`; shard-count probe |
| Aggregate-accounting rehashes lacked immediate deadline guards. | Python and Node route every retained-byte accounting rehash through an immediate before/after monotonic deadline guard; the accepted accounting probe checks the exact stage sequence. | `transport_accounting_identity_accepts`; deadline-overflow probe; parity validator output |

## Exact packet inventory

The final generated packet contains:

- 54 closed protocol types;
- 122 canonical object preimages and 2 raw preimages;
- 34 exact digest links;
- 25 rules, 19 authority-bearing, and 352 role mappings;
- 149 full owner/repository/linkage authority edges;
- 388 differential cases: 54 accepted transitions and 334 expected rejections;
- 10 raw lexical cases: 3 accepted and 7 expected rejections;
- 5 closed transport conformance cases: 1 accepted accounting/deadline-guard identity and 4 rejection probes;
- one source audit covering all 388 cases, including 360 authority cases, 3,257 explicit source store tuples, 331 explicit vote facts, 3,590 exact final receipts, and 10 registered mutations.

Hard-pinned authority identities are:

```text
authority edge registry  sha256:639db97c3707b75470aceba0d9534d01f2624c50fc3d722b262c2033f3eb1a81
authority role manifest  sha256:d8ce4592efbac65f59fdf9f0fde75cb418be5ca7ab10822d44622c0ed48e2bb5
source explicitness audit sha256:9746fbd11e24fc5d7fa5a4a0bce01dd1831e5e0b83f089fe583c07bd42a5584e
```

## Exact bounded shard inventory

| Path | Bytes | Raw-file SHA-256 | Cases | Raw cases |
|---|---:|---|---:|---:|
| `differential-fixtures-shard-000.json` | 12,547,260 | `00664328381e1331c62281f1c4de8b55589d68841a8b67dd1af150c92b535fbb` | 152 | 0 |
| `differential-fixtures-shard-001.json` | 12,566,206 | `f8a5032ca0dad142064c5b820cdc2ceaa27369a620467759afe52e682d2b09ee` | 137 | 0 |
| `differential-fixtures-shard-002.json` | 10,223,085 | `42bfde24954662fbeffe06e9b06332e159b44bf5863e5673838d0c903dc7292d` | 99 | 10 |

All shards are strictly below 16 MiB and at or below the 12-MiB generator target. Their exact total is **35,336,551 bytes**. Python and Node independently reconstruct:

```text
case_count=388
raw_case_count=10
aggregate_sha256=2d651129475386858a471b31eec3a4e6ea055891587c980a6562a625303242cc
```

## Exact generated-artifact inventory

| Artifact | Bytes | Raw-file SHA-256 |
|---|---:|---|
| `protocol.schema.json` | 170,881 | `ea1a7388ab3065671ba04dd0c4cfb833c1d0d6599df8e905b9b50392623afd07` |
| `golden-fixtures.json` | 1,803,231 | `7c06b88d017849daa37855ee3cec2746aa6a6e914458a551c894685299773aeb` |
| `differential-fixtures.json` | 10,623,079 | `efa2b6918a0f5f6a0ddd1aee8593588c18c51ef30a522e3e3a555ef1b2d8fd60` |

The exact aggregate retained JSON transport size—schema + golden + differential manifest + all three shards—is **47,933,742 bytes**.

## Validation record

The exact packet is checked with:

```text
python3 docs/project/semantic-release-v0/generate_fixtures.py  # twice; shard set included
python3 docs/project/semantic-release-v0/validate_fixtures.py
node docs/project/semantic-release-v0/validate_fixtures.mjs
node ~/ai-society/core/agent-scripts/scripts/docs-list.mjs --docs . --strict
./scripts/ci/full.sh
git diff --check
```

Both validators report 54 types, 122 objects, 34 links, 25 rules/19 authority-bearing/352 mappings, 149 edges, 388 cases, 10 raw cases, 5 transport probes, the complete 3,257/331/3,590/10 source audit, three bounded shards, aggregate `2d651129475386858a471b31eec3a4e6ea055891587c980a6562a625303242cc`, aggregate transport size `47,933,742`, and `PASS`. Convergence, docs-strict, full-gate, and diff checks are rerun against this final packet.

## Legal posture and coverage limits

This packet is proposal-stage architecture and deterministic conformance evidence only. `live_acquisition_implemented=false` remains mandatory. It does not prove live capability distribution, authenticated owner-store reads, action-time freshness under races, filesystem crash behavior, signing/key infrastructure, deployment, canary operation, or operational rollback.

It is not an ADR, implementation authorization, release approval, publication, withdrawal, revocation, owner consent, task creation, canary activation, default, fleet rollout, ontology mutation, or Agent Kernel state change. Decision `52` remains development-only. Decision `53` remains `review_pending` pending fresh strict review of this exact revision, an accepted ADR, separately authorized implementation and validation/rollout/rollback plans, owner-scoped coordination, and authoritative AK unblocking.

The finite 149-edge registry and 388-case audit prove declared tuple execution, bounded transport, and normalized semantic drift; they do not prove reviewer completeness or live owner correctness. No Agent Kernel record was mutated.
