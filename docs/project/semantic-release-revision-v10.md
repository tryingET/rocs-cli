---
summary: "Decision:53 semantic-release revision v10 strict-blocker closure and deterministic validation record."
read_when:
  - "Reviewing Decision:53 revision v10 or the revision-v9 strict-review closure."
type: "revision_note"
status: "proposed"
rfc_revision: "semantic-release-revision-v10"
review_posture: "fresh_review_required"
---
# Semantic Release Revision v10

## Objective and controlling review

Revision v10 answers the controlling [`semantic-release-rereview9-synthesis-v9.md`](semantic-release-rereview9-synthesis-v9.md) and its governance, owner, and ROCS lanes. It aligns the RFC, [normative invariants](semantic-release-v0/invariants.md), schema, generators, fixtures, and independent validators on the six strict blockers found in revision v9.

## Exact strict-blocker closure

| Revision-v9 blocker | Revision-v10 closure | Direct fixture or mechanical gate |
|---|---|---|
| Capability distributions could be coherently rewritten across config and receipts. | Every receipt-source manifest mapping hard-pins acquisition contract, contract digest, distribution digest, and capability digest. Pins are self-digested and receipts repeat the pin digest. Config, pin, receipt, verifier binding, and manifest must agree. | `authority_coherent_acquisition_rewrite_rejected`; `authority_coherent_owner_repository_rewrite_rejected`; `authority_acquisition_distribution_digest_is_exact` |
| Authority-bearing recovery accepted partial context and conflated journal tuple shape with authorization. | `publication_recovery` requires complete non-null transaction, resulting status, marker, before, and after objects plus exact canonical before-status and prior-journal joins. `publication_journal_shape` is a separate non-authorizing rule that checks only closed enum tuples. | `publication_recovery_null_transaction_rejected`; `publication_recovery_null_result_rejected`; `publication_recovery_null_marker_rejected`; `publication_recovery_null_before_rejected`; `publication_recovery_null_after_rejected`; `publication_recovery_before_status_is_canonical`; `publication_recovery_prior_journal_full_join_is_exact`; `publication_journal_shape_valid_tuple_non_authorizing` |
| Tombstone reuse and projection consumed owner facts without authority classification/currentness. | Both rules are authority-bearing. Tombstone reuse binds the semantic owner's current lifecycle/tombstone head and exact registry owner. Projection binds current tombstones, semantic-owner capsule/registry nodes, and ROCS-owned projection/material proofs. | `tombstone_reuse_stale_registry_rejected`; `tombstone_registry_semantic_owner_substitution_rejected`; `projection_stale_tombstone_registry_rejected`; `projection_capsule_semantic_owner_substitution_rejected`; `projection_rocs_proof_owner_substitution_rejected` |
| Generator canonical defaults could silently supply authority facts. | Every artifact/parameter role and owner-read fact must be explicit before authority wrapping. Only dedicated missing-anchor negatives may omit exactly their named anchor; no canonical value is synthesized and removed later. | `authority_required_anchor_is_mandatory`; `canonical_ak_authority_requires_independent_store_head_fact`; `canonical_ak_authority_requires_independent_current_record_fact`; generator construction assertions |
| Role↔edge validation omitted full owner/repository/linkage semantics. | Every manifest rule carries sorted role-edge links containing edge ID, owner surface/ID, complete repository identity, descriptor-derived role IDs, and linkage digest. Manifest and registry tuples must match field-for-field. | Validator-level bijection, order, owner, repository, role-ID, and `semantic-release.authority-edge-linkage.v10` recomputation over all 105 edges |
| One-edge mutation coverage relied on labels rather than derived semantic change. | Each edge stores a sorted non-empty set of normalized path/old-hash/new-hash descriptors. Python and Node independently build role-keyed semantic views, remove only wrapper/digest-cascade metadata, recompute `semantic-release.semantic-mutation-value.v10` hashes, and derive role IDs. | Independent descriptor and role-linkage recomputation over all 105 positive/drift pairs; empty or wrapper-only mutation rejects |

The generator performs a provisional manifest pass to compute semantic descriptors and a final manifest pass to prove convergence. Manifest digest changes are wrapper metadata and cannot count as semantic mutation.

## Packet inventory and coverage

The revision-v10 packet contains exactly:

- 51 closed protocol types;
- 106 canonical object preimages and 2 raw preimages;
- 34 exact digest links;
- 24 rules, of which 18 are authority-bearing;
- 283 static/prefix role mappings;
- 105 full owner/repository/linkage authority edges;
- 298 differential cases: 50 accepted transitions and 248 expected rejections;
- 8 raw lexical cases: 2 accepted and 6 expected rejections.

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
| `projection` | 3 |
| `publication_cas` | 2 |
| `publication_commit` | 27 |
| `publication_recovery` | 14 |
| `publication_transition` | 2 |
| `rollback` | 10 |
| `tombstone_reuse` | 2 |
| `trust_revocation` | 6 |
| `trust_rotation` | 9 |
| `version_binding` | 1 |
| **Total** | **105** |

`publication_journal_shape` is one of the six non-authority rules and therefore has no authority edge. Its accepted shape witness is deliberately non-authorizing.

## Deterministic packet hashes

After two consecutive generator runs, the generated packet converged byte-for-byte:

```text
protocol.schema.json       d8af497964a962102f91a493b17690d8f90e8d54c36280997dec06bcb678c1bc
golden-fixtures.json       464ced53b6890375d565154a27afc5a084453b073e8ffbdb98fc4cc4055323af
differential-fixtures.json 5e1a11753b8d39a247b1e01dafe0cbfa1641ae748aee3641d19e72783d22c4e0
```

## Validation record

The exact revision-v10 packet was checked with:

```text
python3 docs/project/semantic-release-v0/generate_fixtures.py  # twice
python3 docs/project/semantic-release-v0/validate_fixtures.py
node docs/project/semantic-release-v0/validate_fixtures.mjs
node ~/ai-society/core/agent-scripts/scripts/docs-list.mjs --docs . --strict
./scripts/ci/full.sh
git diff --check
```

Both validators reported the same inventory, full manifest/registry bijection, normalized semantic-mutation recomputation, and `PASS`. The docs strict check, full repository gate, and diff check passed. The second generator run produced the same three hashes and no generated-file delta relative to the first run.

## Legal posture and coverage limits

This packet is proposal-stage architecture and deterministic conformance evidence only. `live_acquisition_implemented=false` remains mandatory. Nothing here proves live capability distribution, authenticated owner-store reads, action-time freshness under races, filesystem crash behavior, signing/key infrastructure, deployment, or operational rollback.

It is not an ADR, implementation authorization, release approval, publication, withdrawal, revocation, owner consent, task creation, canary activation, default, fleet rollout, ontology mutation, or Agent Kernel state change. Decision `52` remains development-only. Decision `53` remains `review_pending` pending fresh strict review of this exact revision, an accepted ADR, separately authorized implementation and validation/rollout/rollback plans, owner-scoped coordination, and authoritative AK unblocking.

The finite 105-edge registry proves declared tuple execution and normalized semantic drift, not that reviewers cannot identify a missing semantic edge. Fresh strict review retains completeness and owner-correctness judgment. No AK record or ontology worktree was read for mutation or changed during this closeout.
