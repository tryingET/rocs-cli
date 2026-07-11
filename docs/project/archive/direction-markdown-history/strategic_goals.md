---
summary: "Historical rocs-cli strategic-goal snapshot retained for migration audit."
read_when:
  - "You are tracing the retired SG/TG/OP decomposition and its completed work."
type: "reference"
---

# Archived strategic goals

> Historical snapshot only. Status language below records the former plan and is not current direction. Use `ak strategy list --repo .`, `ak wave list --repo .`, and AK tasks for live truth.

## Scoring method
Eisenhower-3D inputs:
- Importance: 1-5
- Urgency: 1-5
- Difficulty: 1-5

Higher importance + urgency wins. Lower difficulty breaks ties.

## Candidate directions from current repo truth

| Candidate | Evidence | Importance | Urgency | Difficulty | Decision |
|---|---|---:|---:|---:|---|
| Consolidate shared helper boundaries across bootstrap/audit/remediation so fleet contract logic stops drifting | Active AK tasks `#363`, `#364`; recent hardening commits target these paths directly | 5 | 5 | 3 | **Strategic Goal 1 — active** |
| Keep the post-GitLab local-gate contract truthful across docs, handoff, and validation surfaces | Previous wave closed in `next_session_prompt.md`; repo lacked explicit direction docs before this session | 4 | 4 | 2 | **Strategic Goal 2 — next** |
| Expand new product surface area (new commands/features beyond current contract hardening) | No active repo-local task truth or urgent repo evidence | 2 | 1 | 4 | Excluded as speculative |

## Strategic Goal 1 — active at snapshot time (now historical)
**Eliminate contract drift in downstream fleet helper surfaces.**

Success looks like:
- shared helper seams are explicit and unit-tested
- bootstrap/audit/remediation paths reuse the same contract logic where appropriate
- fresh bootstrap + rerun convergence remain validated

## Strategic Goal 2 — next at snapshot time (not current direction)
**Keep the stabilized local-gate/operator contract truthful and easy to consume.**

Success looks like:
- docs and handoff surfaces match the post-GitLab design
- local operator entrypoints are clear (`scripts/ci/full.sh`, workspace-only refs, local validation)
- validation coverage guards the published contract

## Historical rollover rule
The original snapshot deferred Strategic Goal 2 until its tactical work completed. Do not apply this rule to current AK-native direction.
