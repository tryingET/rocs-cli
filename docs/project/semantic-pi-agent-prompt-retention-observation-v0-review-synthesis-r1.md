---
summary: "Controlling strict-convergence synthesis for Decision 98."
read_when:
  - "Determining Decision 98 ADR readiness."
type: "review_synthesis"
status: "complete"
review_outcome: "ready_for_adr"
decision_id: 98
---
# Review synthesis — correlated Pi agent-prompt observation v0 r1

## Controlling outcome

`ready_for_adr`

The three required lanes reviewed identical bytes at commit `427d8c62bb110812e9946c609c59e1ab14313b95`, aggregate `7ef2e79c2e42ae333e9be90623423363985df9814173e601027ff73df57ab4b0`, and converged with zero blockers and zero unresolved material findings.

## Accepted direction for ADR drafting

- add host capability `prompt.agent-state.observation.v1`;
- correlate `before_agent_start` with new post-assignment `agent_prompt_ready` via one private opaque token;
- keep only the latest package preparation and ignore nonmatching events;
- report whole-prompt `exact_match` or `mismatch`, never infer contribution removal;
- expose deterministic, TUI-only, non-persistent readback without prompt fingerprints;
- implement host, package, deterministic integration, live TUI canary, and empirical evaluation through separate owner tasks;
- keep provider/model/transmission/benefit/default/production claims outside this decision.

## Legal next move

Attach the final problem brief, evidence note, review-set plan, memo, and this controlling synthesis to Decision 98; complete and reevaluate its decision-support tasks; then advance through `decision_pending` and `adr_required` as the AK passport permits. ADR recording remains architecture authority only and does not implement host/package code or authorize runtime/provider/model actions.
