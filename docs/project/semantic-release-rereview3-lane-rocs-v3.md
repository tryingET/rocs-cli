---
summary: "Decision:53 ROCS-lane rereview of semantic-release revision v3."
read_when: ["Revising Decision:53 after revision-v3 review."]
type: "review_memo"
status: "complete"
review_outcome: "revise_rfc"
---
# Decision 53 Rereview v3 — ROCS Lane

## Outcome

`revise_rfc`

Both token-aware validators pass 37 types, 64 objects, 28 links, 117 differential cases, and 7 raw lexical cases. Remaining false accepts:

- archive validation permits extra entries beyond exact payload plus metadata;
- generation accepts a substituted activation object whose digest differs from the current pointer;
- rollback accepts fabricated `history_head_before` not bound to current activation/history;
- issuer-scope checks are not applied to all differential subjects;
- Node raw parsing uses prototype-bearing objects/`in`, losing `__proto__` own fields;
- Node manifest ordering uses UTF-16 rather than normative UTF-8.

These are concrete machine-contract blockers, not prose preferences.
