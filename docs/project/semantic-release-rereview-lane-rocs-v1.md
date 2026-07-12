---
summary: "Decision:53 ROCS-lane rereview of RFC revision v1 machine contracts."
read_when:
  - "Revising Decision:53 after its first machine-contract rereview."
type: "review_memo"
status: "complete"
review_outcome: "revise_rfc"
---
# Decision 53 Rereview v1 — ROCS Lane

## Outcome

`revise_rfc`

Independent checks passed: 222 local references, 32 closed object schemas, 19 unique protocol discriminators, 20 canonical objects, 20 embedded digests, 2 raw preimages, 18 chain links, deterministic regeneration, and 11 differential cases.

Remaining P0:

1. Materialization expected/actual equality is not linked to the capsule-approved payload projection; an internally complete attacker tree can be accepted.
2. Runtime-only rollback lacks semantic `retain`; combined partial outcomes have no stage/journal representation and conflict with failed-state history rules.
3. ROCS generation can reference a revoked/superseded activation; current activated status is not a required invariant.
4. `digest_mismatch` has precedence but no error code, and audit `recorded_at` relies on annotation-only `format` plus a regex that permits impossible dates.
5. Generator and validator share canonicalization code; a genuinely independent language verifier and broader runtime/rollback/revocation/timestamp fixtures remain required.
