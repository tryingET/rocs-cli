---
summary: "Controlling Decision 80 r22 strict-convergence synthesis."
read_when: ["Tracing Decision 80 r22 outcome and legal next move."]
type: "review_synthesis"
status: "complete"
review_outcome: "revise_rfc"
---
# Decision 80 r22 — controlling synthesis

All five required exact-byte lanes completed on commit `b834dc2e3b450483a7f0bfabf8fa88a910d9beb8`, tree `84248c9ddf504672b8fea94ac55e57268b3c58f2`, aggregate `4c874dbbc016b09c5e2ba7b5c17dce20a9f4133ec8e7380a6b421e534eefec4f`.

Strict convergence does not succeed. Pi component and ROCS lanes found that exact pinned source comments contain non-ASCII UTF-8 while r22 leaves ASCII validation versus comment stripping order ambiguous. Governance found that corrected protocol authority remains bound to Decision 71 while Decision 80 is not yet accepted, and required explicit sentinel-branch conformance obligations. These blockers and material improvement cannot be outvoted by the two `ready_for_adr` lanes.

## Controlling outcome

`revise_rfc`

## Required grouped revision

1. Define exact raw preprocessing: verify pinned bytes and reject CR, split on LF, strip bytes from the first ASCII `#` for comment-bearing formats, then require retained syntax bytes to be ASCII before field parsing.
2. Treat Decision 71/r21, failed task 4230, and evidence 5325 as immutable predecessor history. Make Decision 80 supersession conditional on a future accepted ADR and bind corrected packet/runtime/task/ledger authority to Decision 80.
3. Add closed sentinel conformance obligations for valid exact six, extra surrogate, tuple/category/CCC/decomposition drift, and emitted-surrogate rejection; update all exact fixture/coverage counts and derivation rules consistently.
4. Freeze a new fourteen-file identity and rerun all five lanes.

No packet generation, implementation, owner acceptance, host/component work, dogfood, ontology activation, live acquisition, publication, or production action is authorized.
