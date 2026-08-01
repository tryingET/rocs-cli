---
summary: "Strict-convergence review plan for Decision 98."
read_when:
  - "Running Decision 98 architecture review."
type: "review_set_plan"
status: "proposed"
decision_id: 98
---
# Review-set plan — Pi agent-prompt observation v0

## Frozen review target

Freeze one Git commit. The aggregate is SHA-256 over raw Git-object bytes concatenated with no delimiter in this exact order:

1. `semantic-pi-agent-prompt-retention-observation-v0-problem-brief.md`;
2. `semantic-pi-agent-prompt-retention-observation-v0-evidence-note.md`;
3. `semantic-pi-agent-prompt-retention-observation-v0-rfc.md`;
4. `semantic-pi-agent-prompt-retention-observation-v0-review-set-plan.md`.

All lanes reproduce the commit, individual blobs, order, and aggregate.

## Required lanes

### Pi component and host-contract lane

Verify event/token contract, overlap safety, assignment/readback ordering, exact-match semantics, compatibility capability, host and package implementability, and deterministic faux-provider harness feasibility.

### Governance, security, and claim lane

Verify no provider/model/contribution-survival overclaim; no public token or prompt fingerprint; default-off consent; explicit owner boundaries; exact settings rollback; and separate runtime/provider/model authority.

### Product-value and debt lane

Verify deterministic operator states, loaded-source proof, extracted package design below file budgets, B0/B1/B2 separation, live-canary requirements, proportional one-slot state, and deletion/rollback simplicity.

## Verdicts

Each lane returns exactly `ready_for_adr`, `revise_rfc`, or `reject_direction`. Any blocker or unresolved material finding prevents ADR opening. One controlling synthesis cites all lane outputs and the frozen aggregate.

## Review integrity

Review is read-only. Reviewers do not implement, install, reload, dogfood, call providers/models, publish, or move AK lifecycle state. Later host, package, and runtime actions use separate owner tasks.
