---
summary: "Decision:52 lifecycle-aware review lane for cross-owner authority, adoption, rollout, rollback, and ADR legality."
read_when:
  - "Reviewing decision:52 attempt 1 governance findings."
  - "Checking the legal next move for the semantic discovery RFC."
type: "review_memo"
decision_id: 52
review_outcome: "revise_rfc"
---

# Review Lane — Authority, Adoption, and Rollout

## Review chain status

- Review kind: Tier-1 pre-ADR review attempt
- Decision: `52`
- Primary: `semantic-discovery-protocol-v0.md@71a7fdc1bfaaa89e266b123fd9ca5a02fca2144e`
- Companion: `semantic-preflight-adapter-v0.md@f4941909fc2a74128648155b23e078cde0a2c0b2`
- Procedure: Prompt Vault `layer12-070-decision-rfc-review`
- Problem brief, evidence note, and review-set plan: present
- ADR legal now: **no**

## Overall verdict

```text
review_outcome = revise_rfc
next_legal_move = revise_rfc
```

The owner split is promising, but production identity, lifecycle authorization, defaults, rollback, and artifact linkage are not converged.

## Lens 1 — Cross-owner authority and vocabulary

### Must-fixes

1. Do not freeze or implement a `release_capsule` production variant while assigning its meaning to a later decision. Reserve the coordinate only, or bring its owner/schema/approval into this decision.
2. Separate semantic release approval, ROCS executable/tool trust, and consumer adoption/default intent. Name each source owner and how AK references rather than absorbs its facts.
3. Complete controlled-vocabulary preflight with retrieval source, semantic references where applicable, material retrieval/invocation/applicability enums, and runner identities.

### Architecture-shaping question

Does the production capsule identify only immutable semantic corpus content, or also ROCS executable bytes? The reviewed RFCs imply both.

## Lens 2 — Development/default rollout and rollback

### Must-fixes

1. Remove all pre-ADR “may implement” authorization. Every R/P phase is candidate post-ADR sequencing until AK accepts the decision and post-ADR artifacts exist.
2. Separate defaults for explicit ontology search, automatic prompt-run preflight, and startup orientation. Define which authority/evidence gate controls each.
3. Define independent capsule rollback and adapter/runtime rollback. Capsule N-to-N−1 does not recover a broken package, host contract, or runner trust path.
4. Link any later implementation task as `post_adr_execution`; use `decision_support` only for review/ADR work.
5. Require a concrete AK decision coordinate for the later release/adoption dependency before P6 execution can be created or claimed.

### Material improvement required by strict mode

Add a phase matrix covering identity, runner, ranking owner, automatic behavior, task role, required evidence, and rollback for pre-ADR, development dogfood, adopted canary, package default, and fleet phases.

## Lens 3 — Artifact legality and boundedness

### Must-fixes

1. Repair lifecycle links: primary RFC to problem/evidence, evidence to problem, revised RFCs to controlling revise synthesis.
2. Rename the companion “Implementation plan” as candidate post-ADR sequencing; it has no execution authority before ADR.
3. Pin both exact reviewed revisions in every lane and synthesis; any change requires a new attempt.
4. Bound this decision to the target authority split and safe development posture. Production release identity/trust and default rollout remain separate gates.

### Evidence limits

- No discovery implementation, production capsule, adoption protocol, runner trust root, latency proof, agent-outcome proof, lifecycle proof, or rollback proof exists.
- AK's current-track bootstrap cannot prove lane topology without synthesis citing every lane.
- Passport `ready_for_unblocked` is not implementation authority while review/ADR/planning are absent.

## Workflow result

- review outcome: `revise_rfc`
- ADR legal now: no
- controlling rationale:
  - strict convergence has material unresolved items;
  - decision authority leaks into a later release/adoption membrane;
  - pre-ADR implementation language contradicts lifecycle law;
  - rollback and default-cutover gates are incomplete.
- next legal move:
  1. attach all three lane memos;
  2. attach a controlling synthesis with `revise_rfc`;
  3. revise both RFCs together;
  4. run a fresh exact-revision review set.

No ADR drafting, implementation-task creation, implementation, or default cutover is legal now.
