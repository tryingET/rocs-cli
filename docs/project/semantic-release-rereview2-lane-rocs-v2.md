---
summary: "Decision:53 ROCS-lane rereview of semantic-release revision v2."
read_when: ["Revising Decision:53 after revision-v2 review."]
type: "review_memo"
status: "complete"
review_outcome: "revise_rfc"
---
# Decision 53 Rereview v2 — ROCS Lane

## Outcome

`revise_rfc`

Both validators passed 37 types, 58 objects, 23 links, and 74 cases, but shared missing invariants remain:

1. Projection permits duplicate destination paths/unreferenced consumer paths; capsule archive metadata linkage is cyclic/indirect.
2. Failed/partial rollback receipts can omit failed/completed stages and preserve or mutate history inconsistently.
3. Generation currentness omits coordinate/runtime equality with activation.
4. Node/Python strict JSON and UTC differ: duplicate keys and numeric lexical forms are lost by `JSON.parse`/Python `int`, and Node accepts year zero.
5. The independent Node verifier trusts fixture-supplied domains/omissions and does not independently enforce all ordering/uniqueness.

`digest_mismatch` is closed. Add re-digested counterexamples and raw-token-aware parsing in both languages.
