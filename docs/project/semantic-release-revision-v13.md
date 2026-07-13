---
summary: "Decision:53 semantic-release corrected revision v13 fresh-review closure and bounded-shard validation record."
read_when:
  - "Reviewing Decision:53 corrected revision v13 or its fresh-review closure."
type: "revision_note"
status: "proposed"
rfc_revision: "semantic-release-revision-v13"
review_posture: "fresh_review_required"
---
# Semantic Release Revision v13

## Objective and controlling review

This corrected packet retains the `semantic-release-revision-v13` name and every existing path. It preserves the closure of the controlling [`semantic-release-rereview12-synthesis-v12.md`](semantic-release-rereview12-synthesis-v12.md) and [`semantic-release-rereview12-greats-adjudication-v12.md`](semantic-release-rereview12-greats-adjudication-v12.md), and closes the five fresh review findings in the same RFC, invariants, generator, generated corpus, and independent Python/Node validators. It remains an offline proposal packet for fresh strict review. No Agent Kernel state was read or mutated because the AK runtime is temporarily schema-incompatible.

## Original v13 blocker closure

| Rereview12 blocker | Revision-v13 closure | Direct evidence |
|---|---|---|
| Recovery accepted a caller-supplied expected action and publication transactions omitted the complete approval action. | `semantic-publication-transaction.v0` now carries closed `approved_action` and `approved_action_digest`. Publish derives `release` with transaction coordinate/candidate capsule and transaction-bound source/report. Withdraw/revoke derive the complete action from operation, transaction reason/CAS fields, resolved prior status, and current policy/set/predicate. Approval action/digest must equal transaction and derived action/digest. Recovery has no `expected_action` parameter. | `publication_recovery_coherent_wrong_action_kind_rejected`; `publication_recovery_coherent_wrong_action_coordinate_rejected` |
| Recovery-start state treated post-CAS recovery as if it still observed the prior head. | Pre-linearization canonical/before state is exactly prior and discard leaves after at prior. Post-linearization canonical/before state is exactly result; completion leaves after at result and cannot perform a second CAS. | `recovery_prelinearization_observed_start_must_be_prior`; `recovery_postlinearization_observed_start_must_be_result`; `recovery_postlinearization_forbids_second_cas` |
| Single-canary repository/scope stopped before generation and Pi delivery. | ROCS generation and every delivered/suppressed/failed Pi variant carry exact `consumer_repository` and `v0_canary_scope`. Generation binds both to activation; every Pi variant binds both to generation. | `generation_canary_scope_must_equal_activation`; `generation_second_canary_rejected`; `generation_default_scope_rejected`; all three `pi_*_canary_scope_drift_rejected` cases |
| Tombstone history could coherently reset genesis and did not bind authorization to the resulting removal/lifecycle head. | Lifecycle, reuse, and projection consume an external capability-pinned semantic-owner genesis anchor fact: owner ID, namespace, genesis registry digest, revision 1, and genesis lifecycle head. History genesis must equal it. Every non-genesis authorization digest equals both resulting registry lifecycle head and exact added-entry removal origin. | `lifecycle_tombstone_genesis_anchor_mismatch_rejected`; `tombstone_history_coherent_genesis_reset_rejected`; `tombstone_history_coordinated_wrong_authorization_rejected`; `projection_tombstone_genesis_anchor_mismatch_rejected` |
| The approximately 39 MiB differential file violated the 16 MiB artifact limit and loaders did not enforce file/depth bounds. | `differential-fixtures.json` is a closed hash-complete manifest. Three deterministic shards carry cases. Python and Node stat before read, enforce per-file byte bounds, strict UTF-8/no BOM, depth ≤64, root-local non-network shard names, exact inventory/no extras, byte/hash/count/index/order, and identical aggregate reconstruction. Generator removes stale shard names before deterministic output. | `raw_nesting_depth_64_accepts`; `raw_nesting_depth_65_rejected`; identical validator aggregate SHA-256 below |


## Corrected-v13 fresh-review closure

| Fresh blocker | Corrected revision-v13 closure | Direct evidence |
|---|---|---|
| A non-genesis tombstone delta could replay an existing ID without growing the registry, and lifecycle heads could no-op or roll back. | Every added ID is absent from every earlier registry, cumulative cardinality is exactly prior `+1`, prior head equals the immediately preceding head, resulting head is current and fresh across all prior heads, and all cumulative bytes remain exact. | `tombstone_history_replayed_added_id_rejected`; `tombstone_history_lifecycle_head_noop_rejected`; `tombstone_history_lifecycle_head_rollback_rejected` |
| Recovery had no accepted idempotent `committed/linearized/none` re-entry. | The committed branch requires canonical/before/after/result equality, the exact durable marker already present, explicit null intent, no staging, `recovery_action=none`, and therefore no CAS or mutation. Marker drift, state mutation, and intent/staging reappearance reject. | `recovery_committed_replay_is_idempotent`; `recovery_committed_replay_marker_drift_rejected`; `recovery_committed_replay_mutation_rejected`; `recovery_committed_replay_intent_or_staging_rejected` |
| Shard bytes were parsed before raw authentication and path-stat/read was raceable. | Both loaders no-follow-open, `fstat` a regular file bounded to 16 MiB, read at most `limit+1`, verify descriptor and current-path device/inode/mode/size/mtime/ctime stability, reject symlink/replace/grow/truncate/mutate, hash raw bytes and compare shard length/hash, then decode and parse. | Python `load_json_bytes`; Node `loadBytes`; identical authenticated shard inventory and aggregate below |
| ROCS generation and Pi delivery checked issuer kind but not exact adapter ID. | Generation requires `{kind: rocs, id: rocs-cli}` against pinned `rocs-owner/rocs-cli` identity; Pi requires `{kind: pi, id: pi-adapter}` against pinned `pi-owner/pi-adapter` identity. | `generation_issuer_id_must_match_pinned_rocs_adapter`; `pi_issuer_id_must_match_pinned_delivery_adapter` |
| `ak_optional_pi` returned unconditional success. | Exact AK issuer ID is enforced. A capability-pinned canonical AK task-state receipt resolves task and accepted evidence; typed decision, activation, generation, and optional Pi nodes are self-digest/issuer/repository validated and every linkage is equal. Pi is explicitly null for generation-only lineage or exactly resolved for delivery. | Both accepted AK variants plus direct issuer/task/decision/evidence/activation/generation/Pi/nullability drift negatives listed below |

## Packet inventory

The generated revision-v13 packet contains:

- 54 closed protocol types;
- 122 canonical object preimages and 2 raw preimages;
- 34 exact digest links;
- 25 rules, 18 authority-bearing, and 348 role mappings;
- 139 full owner/repository/linkage authority edges;
- 375 differential cases: 51 accepted transitions and 324 expected rejections;
- 10 raw lexical cases: 3 accepted and 7 expected rejections;
- one full source audit covering all 375 cases, 3,225 explicit source store tuples, 329 explicit vote facts, 3,556 exact final receipts, and 10 registered mutations.

Hard-pinned authority identities are:

```text
authority edge registry  sha256:a1b26aefb4c9c6746e646d8b443d24cd2ef8024123cf45cfa58adae645303130
authority role manifest  sha256:62ae94c1ed3a9e5609087fa753cd820340b7caf10cb142eeb019f9ddf42ccf28
source explicitness audit sha256:e8b4bc0396b01e4e55b23583dc440c60b11eb1f5a523b49fe418b10e2b170390
```

## Bounded shard inventory

The manifest's UTF-8-sorted inventory is:

| Path | Bytes | SHA-256 | Cases | Raw cases |
|---|---:|---|---:|---:|
| `differential-fixtures-shard-000.json` | 12,580,683 | `9a3f32ee416b35b461a082fa2fe0f56e0c918ae2eb6ac91d5bb0565120f741ac` | 158 | 0 |
| `differential-fixtures-shard-001.json` | 12,554,532 | `381012c23cf5ae38b62cc1e30e4897d940a233c01946d6e21a733cc9a4bc340a` | 132 | 0 |
| `differential-fixtures-shard-002.json` | 8,415,235 | `31ee335f271e57650d1a43cd2f5d2ebcce3e6cf94c7a195e9c9d7a8e2cdf35bc` | 85 | 10 |

All shards are below 16 MiB and at or below the 12 MiB generator target. Their total is 33,550,450 bytes. Python and Node independently reconstruct:

```text
case_count=375
raw_case_count=10
aggregate_sha256=ce1107008d5cfe0ebf091a4450344bb1f3512ead7843a5ff13b9c682dfb961e3
```

All generated JSON artifacts are within 16 MiB:

| Artifact | Bytes | File SHA-256 |
|---|---:|---|
| `protocol.schema.json` | 170,171 | `5a0f6b3bc42020d70843b4223d2d8c2eca73e3614b3cb4691c4d627b6969a257` |
| `golden-fixtures.json` | 1,762,296 | `ff2c059ac8cb48cb485f7efce8fcfdce62163d11ef07e6669592946ae168184d` |
| `differential-fixtures.json` | 9,369,691 | `194256970952c790fc0097c4cb794ad1359b969a7d1baf9c5d96944eb00b1cbe` |

## Fresh correction fixture names

```text
tombstone_history_replayed_added_id_rejected
tombstone_history_lifecycle_head_noop_rejected
tombstone_history_lifecycle_head_rollback_rejected
recovery_committed_replay_is_idempotent
recovery_committed_replay_marker_drift_rejected
recovery_committed_replay_mutation_rejected
recovery_committed_replay_intent_or_staging_rejected
generation_issuer_id_must_match_pinned_rocs_adapter
pi_issuer_id_must_match_pinned_delivery_adapter
ak_linkage_issuer_id_must_match_pinned_adapter
ak_linkage_task_reference_drift_rejected
ak_linkage_decision_reference_drift_rejected
ak_linkage_evidence_reference_drift_rejected
ak_linkage_activation_reference_drift_rejected
ak_linkage_generation_reference_drift_rejected
ak_linkage_pi_reference_drift_rejected
ak_generation_only_requires_null_resolved_pi
ak_delivery_claim_requires_resolved_pi
```

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

Both validators report 54 types, 122 objects, 139 edges, 375 cases, 10 raw cases, the complete source/final audit, three bounded shards, aggregate `ce1107008d5cfe0ebf091a4450344bb1f3512ead7843a5ff13b9c682dfb961e3`, and `PASS`. The convergence, docs-strict, full-gate, and diff results are recorded after the final rerun below.

## Legal posture and coverage limits

This packet is proposal-stage architecture and deterministic conformance evidence only. `live_acquisition_implemented=false` remains mandatory. It does not prove live capability distribution, authenticated owner-store reads, action-time freshness under races, filesystem crash behavior, signing/key infrastructure, deployment, canary operation, or operational rollback.

It is not an ADR, implementation authorization, release approval, publication, withdrawal, revocation, owner consent, task creation, canary activation, default, fleet rollout, ontology mutation, or Agent Kernel state change. Decision `52` remains development-only. Decision `53` remains `review_pending` pending fresh strict review of this exact revision, an accepted ADR, separately authorized implementation and validation/rollout/rollback plans, owner-scoped coordination, and authoritative AK unblocking.

The finite 139-edge registry and 375-case audit prove declared tuple execution, bounded transport, and normalized semantic drift; they do not prove reviewer completeness or live owner correctness. No AK record was mutated and no commit was created during this revision.
