---
summary: "Decision:52 attempt-2 authority and lifecycle re-review lane."
read_when:
  - "Reviewing decision:52 attempt-2 governance findings."
type: "review_memo"
decision_id: 52
review_outcome: "revise_rfc"
---
# Re-review Lane — Authority and Lifecycle v1

Reviewed `semantic-discovery-protocol-v0.md@c9591ba`, companion `semantic-preflight-adapter-v0.md@45fb944f`, prior synthesis, lifecycle artifacts, and decision:52 passport under Prompt Vault `layer12-070-decision-rfc-review`.

## Closed
Pre-ADR implementation permission is removed; semantic, tool, adoption, AK, and Pi owner categories are substantially separated; default phases and rollback classes are improved.

## Remaining strict blockers

1. The required later production decision has no concrete AK coordinate.
2. The startup-context event assigns behavior to another owner without acceptance; it must be producer-only/deferred.
3. Production terminology remains inconsistent and the vocabulary table is malformed/incomplete.
4. No normative projection table maps machine dimensions to five outcomes.
5. Pi P0 uses stale effective-request naming.
6. P6 is canary-only but earlier text still names P6 as search cutover; P7 now owns that move.
7. Phase matrices omit some required owner/evidence/task/rollback fields and first canary lacks disable-to-current fallback.

ADR is not legal while decision:52 remains in review with controlling `revise_rfc` closure.

Exactly three lenses were applied: authority/lifecycle legality; vocabulary/contract convergence; defaults/rollback/task gating.

```text
review_outcome = revise_rfc
next_legal_move = revise_rfc
```
