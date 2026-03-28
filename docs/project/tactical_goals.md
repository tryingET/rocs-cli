---
summary: "Tactical decomposition for the single active rocs-cli strategic goal."
read_when:
  - "You need the medium-sized repo-local waves under the active strategic goal"
  - "You are deciding whether to refresh the operating plan or promote the next tactic"
type: "reference"
---

# Tactical goals

Active strategic goal: **Strategic Goal 1 — eliminate contract drift in downstream fleet helper surfaces**.

## Tactical Goal 1 — complete
**Close the workspace-only ref-resolution wave and reconcile stale task truth.**

Evidence of completion:
- current branch already carries the workspace-only ref-resolution closure
- `next_session_prompt.md` from the previous wave records that closure
- AK task `#329` is the stale carry-over for that now-complete wave and should be closed, not treated as new ready work

## Tactical Goal 2 — active
**Remove the remaining bootstrap/audit helper drift with shared, directly tested seams.**

Why active now:
- AK already contains concrete repo-local work for it: `#363`, `#364`
- the most recent code work in this repo already clustered around bootstrap/audit/remediation contract hardening
- this is the highest-leverage unfinished repo-local wave after closing the ref-resolution slice

Exit criteria:
- include-remediation logic is modularized behind directly unit-tested helpers
- shared FCOS gate contract helpers are extracted where bootstrap/audit currently drift
- touched surfaces still pass fresh-bootstrap and rerun convergence validation

## Tactical Goal 3 — next
**Refresh docs/operator surfaces only after Tactical Goal 2 stabilizes the helper boundary.**

Why next instead of active:
- the repo now has truthful direction docs and handoff, so the immediate planning gap is closed
- doc/operator cleanup should reflect the stabilized helper surface, not race ahead of it
- avoid creating non-active backlog beyond the smallest truthful next wave
