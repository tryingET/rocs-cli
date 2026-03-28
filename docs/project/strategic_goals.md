---
summary: "Top strategic goals for rocs-cli selected from repo reality with Eisenhower-3D."
read_when:
  - "You need the current strategic ranking before creating tactics or tasks"
  - "You are checking whether the active strategic goal should roll over"
type: "reference"
---

# Strategic goals

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

## Strategic Goal 1 — active
**Eliminate contract drift in downstream fleet helper surfaces.**

Success looks like:
- shared helper seams are explicit and unit-tested
- bootstrap/audit/remediation paths reuse the same contract logic where appropriate
- fresh bootstrap + rerun convergence remain validated

## Strategic Goal 2 — next
**Keep the stabilized local-gate/operator contract truthful and easy to consume.**

Success looks like:
- docs and handoff surfaces match the post-GitLab design
- local operator entrypoints are clear (`scripts/ci/full.sh`, workspace-only refs, local validation)
- validation coverage guards the published contract

## Rollover rule
Do not promote Strategic Goal 2 until the active tactical work under Strategic Goal 1 is materially complete.
