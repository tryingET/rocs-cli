---
summary: "Decision:53 semantic-release revision v13 rereview12 blocker closure and bounded-shard validation record."
read_when:
  - "Reviewing Decision:53 revision v13 or rereview12 closure."
type: "revision_note"
status: "proposed"
rfc_revision: "semantic-release-revision-v13"
review_posture: "fresh_review_required"
---
# Semantic Release Revision v13

## Objective and controlling review

Revision v13 answers the controlling [`semantic-release-rereview12-synthesis-v12.md`](semantic-release-rereview12-synthesis-v12.md) and [`semantic-release-rereview12-greats-adjudication-v12.md`](semantic-release-rereview12-greats-adjudication-v12.md). It closes the five finite rereview12 blockers in the RFC, normative invariants, schema, generator, generated corpus, and independent Python/Node validators. This remains an offline proposal packet for fresh strict review.

## Exact blocker closure

| Rereview12 blocker | Revision-v13 closure | Direct evidence |
|---|---|---|
| Recovery accepted a caller-supplied expected action and publication transactions omitted the complete approval action. | `semantic-publication-transaction.v0` now carries closed `approved_action` and `approved_action_digest`. Publish derives `release` with transaction coordinate/candidate capsule and transaction-bound source/report. Withdraw/revoke derive the complete action from operation, transaction reason/CAS fields, resolved prior status, and current policy/set/predicate. Approval action/digest must equal transaction and derived action/digest. Recovery has no `expected_action` parameter. | `publication_recovery_coherent_wrong_action_kind_rejected`; `publication_recovery_coherent_wrong_action_coordinate_rejected` |
| Recovery-start state treated post-CAS recovery as if it still observed the prior head. | Pre-linearization canonical/before state is exactly prior and discard leaves after at prior. Post-linearization canonical/before state is exactly result; completion leaves after at result and cannot perform a second CAS. | `recovery_prelinearization_observed_start_must_be_prior`; `recovery_postlinearization_observed_start_must_be_result`; `recovery_postlinearization_forbids_second_cas` |
| Single-canary repository/scope stopped before generation and Pi delivery. | ROCS generation and every delivered/suppressed/failed Pi variant carry exact `consumer_repository` and `v0_canary_scope`. Generation binds both to activation; every Pi variant binds both to generation. | `generation_canary_scope_must_equal_activation`; `generation_second_canary_rejected`; `generation_default_scope_rejected`; all three `pi_*_canary_scope_drift_rejected` cases |
| Tombstone history could coherently reset genesis and did not bind authorization to the resulting removal/lifecycle head. | Lifecycle, reuse, and projection consume an external capability-pinned semantic-owner genesis anchor fact: owner ID, namespace, genesis registry digest, revision 1, and genesis lifecycle head. History genesis must equal it. Every non-genesis authorization digest equals both resulting registry lifecycle head and exact added-entry removal origin. | `lifecycle_tombstone_genesis_anchor_mismatch_rejected`; `tombstone_history_coherent_genesis_reset_rejected`; `tombstone_history_coordinated_wrong_authorization_rejected`; `projection_tombstone_genesis_anchor_mismatch_rejected` |
| The approximately 39 MiB differential file violated the 16 MiB artifact limit and loaders did not enforce file/depth bounds. | `differential-fixtures.json` is a closed hash-complete manifest. Three deterministic shards carry cases. Python and Node stat before read, enforce per-file byte bounds, strict UTF-8/no BOM, depth ≤64, root-local non-network shard names, exact inventory/no extras, byte/hash/count/index/order, and identical aggregate reconstruction. Generator removes stale shard names before deterministic output. | `raw_nesting_depth_64_accepts`; `raw_nesting_depth_65_rejected`; identical validator aggregate SHA-256 below |

## Packet inventory

The generated revision-v13 packet contains:

- 54 closed protocol types;
- 120 canonical object preimages and 2 raw preimages;
- 34 exact digest links;
- 25 rules, 18 authority-bearing, and 343 role mappings;
- 139 full owner/repository/linkage authority edges;
- 357 differential cases: 50 accepted transitions and 307 expected rejections;
- 10 raw lexical cases: 3 accepted and 7 expected rejections;
- one full source audit covering all 357 cases, 3,117 explicit source store tuples, 321 explicit vote facts, 3,440 exact final receipts, and 10 registered mutations.

Hard-pinned authority identities are:

```text
authority edge registry  sha256:a1b26aefb4c9c6746e646d8b443d24cd2ef8024123cf45cfa58adae645303130
authority role manifest  sha256:a96179f5e15b017823f7124bc8ebd8eb807fbe27cdc1367e23b0887b8a3966e8
source explicitness audit sha256:9259e5d167428e5573df1f389590f8e2009b7e7d353a0279beb7c23cabc13705
```

## Bounded shard inventory

The manifest's UTF-8-sorted inventory is:

| Path | Bytes | SHA-256 | Cases | Raw cases |
|---|---:|---|---:|---:|
| `differential-fixtures-shard-000.json` | 12,479,786 | `9ee6536b6f81cb3363e305ee9756fbc42aa73b293ba1b7ddb0b267be70180f47` | 155 | 0 |
| `differential-fixtures-shard-001.json` | 12,544,622 | `6ecea9de711de8d7d32c200ab7bf105314910f019d4c492502e217e125fece8c` | 129 | 0 |
| `differential-fixtures-shard-002.json` | 7,365,575 | `663a4b8c52c381cfc3efbb9a86f019a9decd3d850bab7302e103d4d88660b33d` | 73 | 10 |

All shards are below 16 MiB and at or below the 12 MiB generator target. Their total is 32,389,983 bytes. Python and Node independently reconstruct:

```text
case_count=357
raw_case_count=10
aggregate_sha256=73cc235473b2dc5a210c02c285b30b4f97207220f16c3520d2b4c3e27df45aa6
```

All generated JSON artifacts are within 16 MiB:

| Artifact | Bytes | File SHA-256 |
|---|---:|---|
| `protocol.schema.json` | 170,171 | `5a0f6b3bc42020d70843b4223d2d8c2eca73e3614b3cb4691c4d627b6969a257` |
| `golden-fixtures.json` | 1,747,267 | `392bc4161204d4d122bbe7d936d7c304f2664152aa78f326782ea19d2ea352be` |
| `differential-fixtures.json` | 9,071,075 | `c1024694da969e25b6338c0f4f876114035e24e8b5a0f5fd55c2e64ee7ce7490` |

## New fixture names

```text
publication_recovery_coherent_wrong_action_kind_rejected
publication_recovery_coherent_wrong_action_coordinate_rejected
recovery_prelinearization_observed_start_must_be_prior
recovery_postlinearization_observed_start_must_be_result
recovery_postlinearization_forbids_second_cas
generation_canary_scope_must_equal_activation
generation_second_canary_rejected
generation_default_scope_rejected
pi_delivered_canary_scope_drift_rejected
pi_suppressed_canary_scope_drift_rejected
pi_failed_canary_scope_drift_rejected
lifecycle_tombstone_genesis_anchor_mismatch_rejected
tombstone_history_coherent_genesis_reset_rejected
tombstone_history_coordinated_wrong_authorization_rejected
projection_tombstone_genesis_anchor_mismatch_rejected
raw_nesting_depth_64_accepts
raw_nesting_depth_65_rejected
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

Both validators report 54 types, 120 objects, 139 edges, 357 cases, 10 raw cases, the complete source/final audit, three bounded shards, aggregate `73cc235473b2dc5a210c02c285b30b4f97207220f16c3520d2b4c3e27df45aa6`, and `PASS`. The convergence, docs-strict, full-gate, and diff results are recorded after the final rerun below.

## Legal posture and coverage limits

This packet is proposal-stage architecture and deterministic conformance evidence only. `live_acquisition_implemented=false` remains mandatory. It does not prove live capability distribution, authenticated owner-store reads, action-time freshness under races, filesystem crash behavior, signing/key infrastructure, deployment, canary operation, or operational rollback.

It is not an ADR, implementation authorization, release approval, publication, withdrawal, revocation, owner consent, task creation, canary activation, default, fleet rollout, ontology mutation, or Agent Kernel state change. Decision `52` remains development-only. Decision `53` remains `review_pending` pending fresh strict review of this exact revision, an accepted ADR, separately authorized implementation and validation/rollout/rollback plans, owner-scoped coordination, and authoritative AK unblocking.

The finite 139-edge registry and 357-case audit prove declared tuple execution, bounded transport, and normalized semantic drift; they do not prove reviewer completeness or live owner correctness. No AK record was mutated and no commit was created during this revision.
