---
summary: "Decision:52 attempt-2 ROCS protocol re-review lane."
read_when:
  - "Reviewing decision:52 attempt-2 ROCS findings."
type: "review_memo"
decision_id: 52
review_outcome: "revise_rfc"
---
# Re-review Lane — ROCS Protocol v1

Reviewed `semantic-discovery-protocol-v0.md@c9591ba` and companion `semantic-preflight-adapter-v0.md@45fb944f` under Prompt Vault `review-rfc-multi`.

## Closed
Identity domains, Unicode pin, bound-pack direction, JSON transport, capability owner, ranking order, and major top-K semantics are materially improved.

## Remaining strict blockers

1. Snapshot manifest omits resolved-ref/logical-root facts and closed logical-path construction.
2. Caller/effective/result/pack/tool digest preimages lack closed object schemas.
3. Repeated matching values, negative evidence, and `matched_query_tokens` remain ambiguous.
4. Limit ranges/accounting and error-to-kind/null-digest mapping remain incomplete.
5. Automatic subprocess environment lacks exact names/values.
6. ROCS maximum result size conflicts with Pi decoded-JSON cap; Pi query canonicalization conflicts with ROCS raw-byte ownership.

Exactly three lenses were applied: identity/provenance; lexical/limits/errors; transport/effects/cross-runtime alignment.

```text
review_outcome = revise_rfc
```
