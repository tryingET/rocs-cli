---
summary: "Decision:53 semantic-release revision v12 rereview11 blocker closure and deterministic validation record."
read_when:
  - "Reviewing Decision:53 revision v12 or the revision-v11 strict-review closure."
type: "revision_note"
status: "proposed"
rfc_revision: "semantic-release-revision-v12"
review_posture: "fresh_review_required"
---
# Semantic Release Revision v12

## Objective and controlling review

Revision v12 answers the controlling [`semantic-release-rereview11-synthesis-v11.md`](semantic-release-rereview11-synthesis-v11.md) and [`semantic-release-rereview11-greats-adjudication-v11.md`](semantic-release-rereview11-greats-adjudication-v11.md). No foundational architecture contradiction remained; this packet closes the five finite revision-v11 blockers in the RFC, [normative invariants](semantic-release-v0/invariants.md), schema, generator, fixtures, and independent Python and Node validators.

## Exact strict-blocker closure

| Revision-v11 blocker | Revision-v12 closure | Direct fixture or mechanical gate |
|---|---|---|
| v0 mixed a globally hard-pinned first consumer with general rename, second-consumer, default, and fleet claims. | v0 is closed to the exact `pi-canary-consumer` repository identity at revision 3 and one `v0CanaryScope`: one operator-named canary, cardinality 1, `single_operator_named_canary`, and `new_protocol_and_decision_required` for expansion. Intent, acceptance, materialization, and activation repeat that scope. Rename is removed from the compatibility categories. The candidate contract is exactly `decision-53-single-canary-consumer`; `protocol_scope_expansion` stops every expansion. | `v0_consumer_repository_is_exact`; `v0_consumer_identity_revision_three_is_exact`; `v0_consumer_locator_is_exact`; `v0_canary_cardinality_is_exactly_one`; `v0_canary_name_requires_operator_authority`; `v0_scope_expansion_requires_new_protocol_and_decision`; `activation_canary_scope_matches_intent_and_acceptance`; `single_canary_consumer_allowed_paths_are_exact` |
| Publication recovery validated transition shape/state without the complete promised publication authority. | Every recovery resolves complete approval, policy, set, predicate, trust root, external trust/revocation facts, capability-pinned canonical AK store/current decision, per-owner votes, and explicit expected operation action. The same publication-authority helper used by commit/transition recomputes threshold, trust currentness, decision currentness, exact action equality/digest, and vote binding. | `publication_recovery_calls_threshold_authority`; `publication_recovery_calls_trust_authority`; `publication_recovery_calls_canonical_decision_authority`; `publication_recovery_calls_exact_action_authority`; publish/withdraw/revoke recovery positives |
| Python and Node differed on disable rollback technical-receipt checks. | Both validators require disable-contract subject = canonical decision rollback-plan digest, rehearsal subject = contract receipt digest, both coordinates null, and both runtimes = active materialization runtime. Six direct negatives exercise each binding. | `disable_contract_subject_must_match_rollback_plan`; `disable_rehearsal_subject_must_match_contract`; both `*_coordinate_must_be_null` and both `*_runtime_must_match_active_runtime` cases |
| The v11 source audit proved declarations but did not compare every complete tuple to the final wrapped receipts when a fixture intentionally mutated a receipt. | Each source/final tuple now records receipt kind, observation ID, role, repository, store ID/head/revision, action epoch, fact schema/digest/value, and decoded vote tuple. Ten add/replace mutations are registered bijectively and linked to non-empty edge descriptors. Both validators reconstruct each expected-final multiset and compare it exactly to every final snapshot receipt. | `semantic-release-source-case-explicitness-audit.v12`: all 343 cases, 2,959 source store tuples, 309 source vote tuples, 3,270 final receipts, and 10 registered mutations; hard-pinned digest and exact reconstruction in both validators |
| A current tombstone registry could still present truncated or restarted ancestry. | New semantic-owner-issued `semantic-tombstone-history-proof.v0` carries every registry revision from revision-1 genesis through current. Cardinality equals current revision; revisions are gap-free; every registry digest/prior link/lifecycle head and genesis/removal-authorized delta is exact; every later delta adds exactly one removal-origin entry; all cumulative entries remain byte-identical. Lifecycle, reuse, and projection consume the complete proof. | `tombstone_history_truncation_rejected`; `tombstone_history_restart_rejected`; `tombstone_history_dropped_revision_rejected`; `tombstone_history_exact_digest_links_required`; `tombstone_history_authorized_delta_required`; dropped/changed cumulative-entry negatives; `projection_complete_tombstone_history_required` |

## Packet inventory and coverage

The revision-v12 packet contains exactly:

- 54 closed protocol types;
- 120 canonical object preimages and 2 raw preimages;
- 34 exact digest links;
- 24 rules, of which 18 are authority-bearing;
- 341 static/prefix/subject/authority-graph role mappings;
- 129 full role-derived ownership/repository/linkage authority edges;
- 343 differential cases: 50 accepted transitions and 293 expected rejections;
- 8 raw lexical cases: 2 accepted and 6 expected rejections;
- one full source-case audit covering all 343 cases, 2,959 explicit source store tuples, 309 explicit source vote tuples, 3,270 exact final receipts, and 10 registered mutations.

Authority-edge coverage remains:

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

`publication_journal_shape` remains non-authorizing and has no edge. Of the 129 authority edges, 116 are closed `single_owner` tuples and 13 enumerate all linked owners under `multi_owner`.

## Deterministic packet hashes

After two consecutive generator runs, the generated packet converged byte-for-byte:

```text
protocol.schema.json       758a7e1ffa6625b44ee569a52e342aafd5ef644c2a6170e5e5a80427b09c323f
golden-fixtures.json       7a91fdd9d6b6ec6ec9762cbc0f7ae55a40973e965ef8090a1b9cc63cb3de5263
differential-fixtures.json 9d6fb772c77793a5c8e9db0a291953081a925b845ce7d14ab839a8232c195c86
```

The hard-pinned source-case audit digest is:

```text
sha256:1fd32053d0c16907af4893c8149b29d1b0303a0afa20f6347c38106195190338
```

## Validation record

The exact revision-v12 packet was checked with:

```text
python3 docs/project/semantic-release-v0/generate_fixtures.py  # twice
python3 docs/project/semantic-release-v0/validate_fixtures.py
node docs/project/semantic-release-v0/validate_fixtures.mjs
node ~/ai-society/core/agent-scripts/scripts/docs-list.mjs --docs . --strict
./scripts/ci/full.sh
git diff --check
```

Both validators reported the same 54 types, 120 objects, 129 edges, 343 cases, full source/final audit counts, manifest/registry ownership bijection, normalized semantic-mutation recomputation, and `PASS`. The docs strict check, full repository gate, and diff check passed. The second generator run produced the same three hashes and no generated-file delta relative to the first run.

## Legal posture and coverage limits

This packet is proposal-stage architecture and deterministic conformance evidence only. `live_acquisition_implemented=false` remains mandatory. Nothing here proves live capability distribution, authenticated owner-store reads, action-time freshness under races, filesystem crash behavior, signing/key infrastructure, deployment, canary operation, or operational rollback.

It is not an ADR, implementation authorization, release approval, publication, withdrawal, revocation, owner consent, task creation, canary activation, default, fleet rollout, ontology mutation, or Agent Kernel state change. Decision `52` remains development-only. Decision `53` remains `review_pending` pending fresh strict review of this exact revision, an accepted ADR, separately authorized implementation and validation/rollout/rollback plans, owner-scoped coordination, and authoritative AK unblocking.

The finite 129-edge registry and 343-case audit prove declared tuple execution and normalized semantic drift, not that reviewers cannot identify a missing semantic edge. Fresh strict review retains completeness and owner-correctness judgment. No AK record was mutated and no commit was created during this revision.
