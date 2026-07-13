---
summary: "Decision:53 ROCS machine-contract lane rereview of revision v4."
read_when: ["Revising Decision:53 after revision-v4 review."]
type: "review_memo"
status: "complete"
review_outcome: "revise_rfc"
---
# Decision 53 Rereview v4 — ROCS Lane

## Outcome

`revise_rfc`

The generated corpus converges and both validators pass 40 types, 75 objects, 28 links, 150 differential cases, and 8 raw cases. Fresh probes still found false accepts or cross-language divergence:

- context objects are not uniformly schema, issuer, ordering, and self-digest validated before relational evaluation;
- activation legality does not resolve acceptance/materialization or bind coordinate, runtime, scope, and epoch ceiling;
- Python boolean equality can satisfy integer/boolean `const` incorrectly;
- Node SemVer comparison loses precision for unbounded digit sequences;
- publication recovery can accept an arbitrary nonexistent resulting-status digest;
- rollback availability remains opaque;
- archive payload root kind is not required to be a directory;
- trust-root key IDs are not checked for ordering/uniqueness.

Machine closure is not ADR-ready.
