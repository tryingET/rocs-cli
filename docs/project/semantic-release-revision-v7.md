---
summary: "Decision:53 semantic-release revision v7 executable closure of rereview-v6 blockers."
read_when:
  - "Reviewing Decision:53 revision v7 or its machine evidence."
type: "revision_note"
status: "proposed"
rfc_revision: "semantic-release-revision-v7"
review_posture: "fresh_review_required"
---
# Semantic Release Revision v7

## Objective and legal posture

This revision closes every finding in [`semantic-release-rereview6-synthesis-v6.md`](semantic-release-rereview6-synthesis-v6.md) and its governance, owner, and ROCS lane memos. It is proposal-stage architecture evidence only. It does not authorize an ADR, implementation, publication, withdrawal, revocation, task creation, consumer consent, activation, default, fleet rollout, or ontology mutation. Decision `53` remains `review_pending` and requires fresh strict review.

## Exact closure and direct fixture map

| v6 finding | Machine closure | Direct negative fixtures |
|---|---|---|
| Canonical AK authority defaulted missing store/current-record facts from its subject | Every authority rule requires independently supplied canonical store head and current decision-record digest; `decisionCurrent` has no subject fallback in either validator. | `canonical_ak_authority_requires_independent_store_head_fact`; `canonical_ak_authority_requires_independent_current_record_fact` |
| Publication trust and transaction joins were incomplete | Publication authority resolves the root plus an external pin and exactly joins namespace, policy, set, root ID/revision/digest; prior journal transaction equals prior status transaction; lifecycle transactions bind coordinate and namespace exactly. | `publication_trust_root_namespace_binds_authority`; `publication_trust_root_policy_binds_authority`; `publication_trust_root_set_binds_authority`; `publication_trust_root_requires_external_canonical_pin`; `prior_journal_transaction_equals_prior_status_transaction`; `lifecycle_transaction_coordinate_is_exact`; `lifecycle_transaction_namespace_is_exact` |
| Activation continuity could drift and Python/Node disagreed on null previous state | Candidate validation reads the canonical prior pointer/revision. Genesis requires an all-null pointer/prior tuple and revision 1; successor resolves that exact prior receipt and uses prior+1. Node normalizes absent/explicit-null previous state exactly as Python does. A candidate cannot already be supplied as the prior head and is promoted only after validation. | `activation_null_pointer_revision_pair_is_atomic`; `activation_candidate_is_not_prior_canonical_head`; existing `activation_current_head_equals_exact_prior`; positive agreement case `activation_genesis_explicit_null_previous_agrees` |
| Rollback requester, activated target, receipt subject, coordinate, and runtime could drift | Request issuer ID equals repository owner; request target equals activated intent and materialization target. Every technical receipt binds an exact subject and applicable coordinate/runtime; semantic rollback binds the retained active runtime. | `rollback_requester_id_equals_consumer_owner`; `rollback_request_target_equals_activated_intent_and_materialization`; `rollback_technical_receipt_binds_exact_subject_digest`; `rollback_technical_receipt_binds_exact_coordinate`; `semantic_rollback_target_requires_runtime_compatibility` |
| Patch SemVer accepted prerelease-only movement | Patch legality now requires equal major/minor and a strictly greater patch integer, independently implemented with arbitrary-length digit-string comparison. | `patch_semver_rejects_prerelease_only_movement` |
| Governance references lacked executable observed state and repository/pairing exactness | Resolved references carry a separate observed canonical repository/head/task/artifact/state object and validate every claimed/observed/state relation. Unresolved dependencies, prerequisites, evidence, and stop facts bind their fact owner's exact repository. Stop kind, condition ID, fact ID, and repository are exact tuples. | `resolved_governance_reference_observed_head_is_exact`; `resolved_governance_reference_observed_task_digest_is_exact`; `resolved_governance_reference_observed_state_is_exact`; `unresolved_dependency_binds_correct_owner_repository`; `stop_condition_id_pairs_exactly`; `stop_condition_fact_id_pairs_exactly`; `stop_condition_repository_pairs_exactly`; positive resolved case `resolved_governance_reference_observation_accepts` |

## Generated packet

Revision v7 contains 44 closed protocol types, 101 canonical object preimages, 2 raw preimages, 28 exact digest links, 234 differential cases, and 8 raw lexical cases. Python and Node independently validate schema closure, primitive contexts, SemVer, canonical preimages, digests, references, publication authority/lifecycle, activation, rollback, and governance contracts. `schema_builder.py` and `generate_fixtures.py` remain the only generated-JSON writers and run offline.

## Validation record

Run from the repository root:

```text
python docs/project/semantic-release-v0/validate_fixtures.py
  PASS — 44 types; 101 objects; 28 links; 234 differential cases (47 accepted, 187 rejected); 8 raw cases
node docs/project/semantic-release-v0/validate_fixtures.mjs
  PASS — same independently recomputed corpus
python docs/project/semantic-release-v0/generate_fixtures.py (twice) plus SHA-256 comparison
  PASS — generated artifacts converge byte-for-byte
node ~/ai-society/core/agent-scripts/scripts/docs-list.mjs --docs . --strict
  PASS
./scripts/ci/full.sh
  PASS
git diff --check
  PASS
```

## Residual risks and coverage limit

- v0 still uses externally pinned local trust roots; signing/key-distribution infrastructure and production crash testing remain out of scope.
- Fixtures establish architecture-contract consistency, not production authorization or empirical runtime behavior.
- Candidate tasks and future evidence remain unresolved; later authorized owners must resolve them against canonical AK state without changing owner repository, required state, or stop-pair semantics.
- No AK record, task, decision state, commit, ontology, runtime source, lockfile, or test tree was mutated by this revision.
