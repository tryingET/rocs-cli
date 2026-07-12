---
summary: "Multi-lane strict review-set plan for decision:52 over the ROCS discovery RFC and Pi preflight companion."
read_when:
  - "Running or auditing decision:52 pre-ADR review."
  - "Checking which review artifacts may control semantic-preflight ADR legality."
type: "review_set_plan"
decision_id: 52
reviewed_artifact: "docs/project/semantic-discovery-protocol-v0.md"
---

# Review-Set Plan — Semantic Discovery and Pi Preflight v0

## Status

Review-set plan for `decision:52` under:

```text
review_closure_mode = multi_lane_requires_synthesis
```

The primary reviewed RFC is:

```text
/home/tryinget/ai-society/core/rocs-cli/docs/project/semantic-discovery-protocol-v0.md
commit: 71a7fdc
```

Required companion input:

```text
/home/tryinget/ai-society/softwareco/owned/pi-extensions/packages/pi-ontology-workflows/docs/project/semantic-preflight-adapter-v0.md
commit: f4941909
```

The review must treat these revisions as one cross-owner proposal. A later change to either document requires a new review attempt.

## Execution plan

```yaml
review_set:
  decision_id: 52
  reviewed_artifact_ref: /home/tryinget/ai-society/core/rocs-cli/docs/project/semantic-discovery-protocol-v0.md@71a7fdc
  required_companion_refs:
    - /home/tryinget/ai-society/softwareco/owned/pi-extensions/packages/pi-ontology-workflows/docs/project/semantic-preflight-adapter-v0.md@f4941909
  outer_host_runtime: pi_sdk
  legal_runtime: ak_decision
  closure_mode: multi_lane_requires_synthesis
  strict_review_convergence: true
  maximum_revision_rounds: 4
  lanes:
    - lane_id: rocs_determinism_and_protocol
      backend_kind: pi_agent
      procedure_ref: prompt-vault:review-rfc-multi
      role: corpus_identity_algorithm_effects_and_contract_review
      output_artifact_ref: docs/project/semantic-preflight-review-lane-rocs-v0.md
    - lane_id: pi_runtime_security_and_lifecycle
      backend_kind: pi_agent
      procedure_ref: prompt-vault:review-rfc-multi
      role: prompt_trust_runner_host_lifecycle_and_operator_review
      output_artifact_ref: docs/project/semantic-preflight-review-lane-pi-v0.md
    - lane_id: authority_adoption_and_rollout
      backend_kind: pi_agent
      procedure_ref: prompt-vault:layer12-070-decision-rfc-review
      role: cross_owner_authority_adoption_rollback_and_adr_legality_review
      output_artifact_ref: docs/project/semantic-preflight-review-lane-governance-v0.md
  synthesis:
    backend_kind: pi_agent
    procedure_ref: prompt-vault:layer12-070-decision-rfc-review
    internal_critique_ref: prompt-vault:many-of-the-greats
    input_artifact_refs:
      - docs/project/semantic-preflight-review-lane-rocs-v0.md
      - docs/project/semantic-preflight-review-lane-pi-v0.md
      - docs/project/semantic-preflight-review-lane-governance-v0.md
    output_artifact_ref: docs/project/semantic-preflight-review-synthesis-v0.md
    legal_effect: closure_candidate
```

## Lane requirements

Every lane must:

- cite the exact RFC and companion revisions;
- distinguish must-fixes, material nice-to-haves, and non-blocking follow-ups;
- list cross-cutting contradictions;
- emit exactly one recommended token:
  - `ready_for_adr`
  - `revise_rfc`
  - `reject_current_direction`;
- identify its evidence limits;
- avoid implementation or AK lifecycle mutation.

## Synthesis rule

The synthesis is the only controlling review closure candidate. It must cite all three lane artifacts and apply strict convergence:

- any must-fix, material nice-to-have, architecture-shaping question, or cross-cutting contradiction forces `revise_rfc`;
- at most one unresolved question may remain only if it is explicitly non-blocking, post-ADR, and owner-routed;
- disagreement between lanes is input to synthesis, not implicit approval;
- `many-of-the-greats` is an internal critique method, not a lifecycle artifact;
- the synthesis must state whether ADR is legally supportable after considering the problem brief, evidence note, review plan, and exact reviewed revisions.

## Non-authorizations

This plan does not authorize:

- ADR drafting before a controlling `ready_for_adr` synthesis;
- implementation or implementation-task creation;
- default Pi preflight enablement;
- Semantic Release Capsule adoption;
- a runtime distribution trust root;
- ontology or AK vocabulary mutation;
- fleet rollout or mandatory enforcement.
