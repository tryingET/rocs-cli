---
summary: "Decision:53 semantic-release revision v11 rereview10 blocker closure and deterministic validation record."
read_when:
  - "Reviewing Decision:53 revision v11 or the revision-v10 strict-review closure."
type: "revision_note"
status: "proposed"
rfc_revision: "semantic-release-revision-v11"
review_posture: "fresh_review_required"
---
# Semantic Release Revision v11

## Objective and controlling review

Revision v11 answers the controlling [`semantic-release-rereview10-synthesis-v10.md`](semantic-release-rereview10-synthesis-v10.md) and its governance, owner, and ROCS lanes. The Greats adjudication found no remaining architecture conflict; this packet closes the finite machine/provenance blockers in the RFC, [normative invariants](semantic-release-v0/invariants.md), schema, generator, fixtures, and independent Python and Node validators.

## Exact strict-blocker closure

| Revision-v10 blocker | Revision-v11 closure | Direct fixture or mechanical gate |
|---|---|---|
| Tombstone reuse and projection did not join complete currentness or permanent registry history. | Tombstone registries carry lifecycle-head digest. Reuse and projection join exact namespace, lifecycle head, registry digest, and revision; resolve the exact prior registry object; enforce revision `prior+1` and preservation of every prior entry. Capsule repeats the complete tuple, and materialization coordinate equals the coordinate constructed from that capsule. | `tombstone_reuse_namespace_currentness_rejected`; `tombstone_reuse_lifecycle_head_currentness_rejected`; `tombstone_reuse_prior_registry_object_is_required`; `tombstone_reuse_append_only_prior_entries_required`; `projection_materialization_coordinate_equals_capsule_coordinate`; projection namespace/head/revision/prior-registry negatives |
| Pre-linearization recovery incorrectly used a durable fsynced marker. | New `semantic-publication-recovery-intent-marker.v0` is recovery-controller-issued and closed to non-durable intent semantics, `fsync_complete=false`, and no durable marker present. Pre-linearization requires this descriptor and forbids a durable commit marker; linearized completion requires the distinct semantic-owner marker. | `recovery_prelinearization_rejects_durable_marker`; `recovery_prelinearization_requires_intent_descriptor`; `recovery_intent_descriptor_cannot_claim_fsync`; `recovery_intent_descriptor_owner_is_exact` |
| Recovery publication receipts could come from unrelated store observations. | Canonical publication revision/head/status, prior journal, current recovery journal, transaction, and expected result revision/head/status are nine semantic-owner receipts with one identical repository/store ID/head/revision/action-epoch tuple. Their values bind the exact transition. | `publication_recovery_current_journal_receipt_is_exact`; `publication_recovery_transition_expectation_is_exact`; four `publication_recovery_store_snapshot_*_drift_rejected` cases; Python/Node coherent-snapshot recomputation |
| Recovery before/after state was unowned parameter data. | New `semantic-publication-recovery-state-receipt.v0` makes before state a semantic-owner proof node and after state a recovery-controller proof node. Both bind semantic owner, controller, epoch, namespace, transaction, current recovery journal, and separate intent/durable-marker state digests. | `recovery_before_state_is_semantic_owner_issued`; `recovery_after_state_is_controller_issued`; `recovery_state_receipt_namespace_is_exact`; null-node negatives |
| Edge owner tuples were labels rather than consequences of linked roles; recovery marker ownership was wrong. | Every descriptor-derived role has an explicit subject, authority-graph, static, or prefix mapping. The generator derives each concrete role owner and emits either one closed `single_owner` tuple or the complete sorted `multi_owner` tuple. Both validators independently compare every role owner to its linked mapping. Durable recovery-marker edges now derive semantic-owner ownership. | 129 registry/manifest ownership objects; 116 single-owner and 13 multi-owner edges; full mapping/registry/linkage bijection and v11 linkage digest recomputation |
| Vote facts and store metadata could still be synthesized while wrapping. | Every one of the 322 source cases is assigned explicit store metadata and vote-source declarations before wrapping. The generator has no `store_metadata` function or vote-generation path, fails on absent/disagreeing declarations, and emits a hard-pinned source-case audit. Python and Node independently verify audit shape, digest, role coverage, fact consumption, owner repository, and vote equality. | `semantic-release-source-case-explicitness-audit.v11`: 2,463 explicit store tuples and 228 explicit vote facts; `no_store_metadata_or_vote_fact_inference` |

## Packet inventory and coverage

The revision-v11 packet contains exactly:

- 53 closed protocol types;
- 118 canonical object preimages and 2 raw preimages;
- 34 exact digest links;
- 24 rules, of which 18 are authority-bearing;
- 327 static/prefix/subject/authority-graph role mappings;
- 129 full role-derived ownership/repository/linkage authority edges;
- 322 differential cases: 50 accepted transitions and 272 expected rejections;
- 8 raw lexical cases: 2 accepted and 6 expected rejections;
- one source-case explicitness audit covering all 322 cases, 2,463 store metadata tuples, and 228 vote-proof facts.

Authority-edge coverage is:

| Rule | Edges |
|---|---:|
| `acceptance_binding` | 1 |
| `activation_binding` | 5 |
| `ak_decision` | 1 |
| `approval_threshold` | 1 |
| `compatibility` | 2 |
| `generation_activation` | 1 |
| `governance_contracts` | 13 |
| `lifecycle` | 5 |
| `projection` | 9 |
| `publication_cas` | 2 |
| `publication_commit` | 27 |
| `publication_recovery` | 27 |
| `publication_transition` | 2 |
| `rollback` | 10 |
| `tombstone_reuse` | 7 |
| `trust_revocation` | 6 |
| `trust_rotation` | 9 |
| `version_binding` | 1 |
| **Total** | **129** |

`publication_journal_shape` remains non-authorizing and has no edge. Of the 129 authority edges, 116 are closed `single_owner` tuples and 13 explicitly enumerate all linked owners under `multi_owner`.

## Deterministic packet hashes

After two consecutive generator runs, the generated packet converged byte-for-byte:

```text
protocol.schema.json       8c0233d922b41ad5254bc2abde084660056036007946d015d13b926bff89840e
golden-fixtures.json       6d40a3768627ed8c7025bfade23ffa8da7adefa7474f26a3395c4c3499e117b6
differential-fixtures.json 4068fa4a04a4acb0fb6fdc8cfb25cf93f44c0e74d0f8bbcfc3e0a3141543f9e1
```

The hard-pinned source-case audit digest is:

```text
sha256:eab630e0c69217c1e1cae18cc09f0e61aba954e494edd681484f2e36e8b6ce39
```

## Validation record

The exact revision-v11 packet was checked with:

```text
python3 docs/project/semantic-release-v0/generate_fixtures.py  # twice
python3 docs/project/semantic-release-v0/validate_fixtures.py
node docs/project/semantic-release-v0/validate_fixtures.mjs
node ~/ai-society/core/agent-scripts/scripts/docs-list.mjs --docs . --strict
./scripts/ci/full.sh
git diff --check
```

Both validators reported the same 53 types, 118 objects, 129 edges, 322 cases, explicit-source audit counts, full manifest/registry ownership bijection, normalized semantic-mutation recomputation, and `PASS`. The docs strict check, full repository gate, and diff check passed. The second generator run produced the same three hashes and no generated-file delta relative to the first run.

## Legal posture and coverage limits

This packet is proposal-stage architecture and deterministic conformance evidence only. `live_acquisition_implemented=false` remains mandatory. Nothing here proves live capability distribution, authenticated owner-store reads, action-time freshness under races, filesystem crash behavior, signing/key infrastructure, deployment, or operational rollback.

It is not an ADR, implementation authorization, release approval, publication, withdrawal, revocation, owner consent, task creation, canary activation, default, fleet rollout, ontology mutation, or Agent Kernel state change. Decision `52` remains development-only. Decision `53` remains `review_pending` pending fresh strict review of this exact revision, an accepted ADR, separately authorized implementation and validation/rollout/rollback plans, owner-scoped coordination, and authoritative AK unblocking.

The finite 129-edge registry and 322-case audit prove declared tuple execution and normalized semantic drift, not that reviewers cannot identify a missing semantic edge. Fresh strict review retains completeness and owner-correctness judgment. No AK record was mutated and no commit was created during this revision.
