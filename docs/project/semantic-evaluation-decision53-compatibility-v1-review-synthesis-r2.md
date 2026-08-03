---
summary: "Corrected controlling Decision 107 synthesis rejecting an adapter without an accepted semantic source."
read_when: ["Determining the legal next move for Decision 107."]
type: "review_synthesis"
status: "complete"
decision_id: 107
review_outcome: "reject_current_direction"
---
# Decision 107 — controlling synthesis r2

## Correction boundary

R1 closure artifacts at commit `7fd55ac` remain non-controlling history. Independent review `dispatch-1785758901963` accepted their substantive rejection, identity, null-ADR boundary, and AK path but found that each lane artifact had not projected the complete AK prerequisite-state check required by the frozen plan. The r2 lane projections and memo record those checks from the original dispatch results. No lane was rerun, no frozen packet was changed, and no substantive judgment changed.

## Exact identity

All four lanes reviewed commit `2ffb8044a7ef56cfa3d343718609b4928514e251`, tree `c4577e180ac753f5867ac43a71c848db71179694`, aggregate `88a9db5c46976ad34940b01a557adb92fb0b9282bd4336533d3b5e6cda6946a2`.

Inputs:

- ROCS r2 projection: `semantic-evaluation-decision53-compatibility-v1-review-lane-rocs-r2.md` / `dispatch-1785758592398`;
- Decision 53 r2 projection: `semantic-evaluation-decision53-compatibility-v1-review-lane-decision53-r2.md` / `dispatch-1785758592398-1`;
- semantic-owner r2 projection: `semantic-evaluation-decision53-compatibility-v1-review-lane-semantic-owner-r2.md` / `dispatch-1785758592399`;
- governance/security r2 projection: `semantic-evaluation-decision53-compatibility-v1-review-lane-governance-security-r2.md` / `dispatch-1785758592400`.

Each records the exact identity, independently checked AK prerequisites, verdict, blockers, material improvements, architecture disagreements, reason, and legal next move. Every lane returns `reject_current_direction` with zero blockers, zero material improvements, and zero architecture-shaping disagreements.

## Synthesis

Decision 107 has no accepted source fact to adapt. Decision 106's rejection is an architecture lifecycle outcome, not a semantic-evaluation result. Decision 105 supplies custody identity and schema evidence but no semantic-owner policy, selected subjects, typed joins, read authority, currentness, verdict vocabulary, or semantic result.

Decision 53 separates semantic-owner compatibility/publication authority, ROCS verification, consumer adoption/activation, AK lineage, and recovery execution. A non-authoritative adapter can translate accepted typed facts; it cannot manufacture the source fact or issue Decision 53 owner conclusions.

A constant `not_evaluable` runtime, placeholder interface, or translation of AK rejection into a domain status would collapse lifecycle state into semantics. A custody/wire checker is a distinct capability requiring a named consumer and new decision.

Future evidence cannot retroactively reopen Decisions 106 or 107. A later adapter needs a fresh accepted upstream interface and new decision/task citing both rejections.

## Controlling outcome

`reject_current_direction`

## Legal next move

1. Attach the r2 review memo and this synthesis, making r2 the latest legal closure.
2. Advance to `decision_pending` without an outcome.
3. Advance to `tasks_reevaluation_pending` with `outcome=rejected` and this synthesis as evidence.
4. Reevaluate task 4626 as `still_valid`, record required evidence, and complete it as successful adjudication.
5. Advance to `unblocked`, retaining `outcome=rejected` and null ADR.
6. Leave Decisions 53, 105, and 106 unchanged.

Final `unblocked/rejected` means linked-task reevaluation is complete. It grants no accepted architecture, ADR, implementation, schema, data access, compatibility verdict, publication, adoption, activation, provider/model/network use, dogfood, production, or push.
