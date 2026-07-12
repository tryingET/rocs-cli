---
summary: "Decision:52 fifth bounded Python/ROCS producer schema review lane."
read_when: ["Checking decision:52 fifth-review producer findings."]
type: "review_memo"
decision_id: 52
review_outcome: "revise_rfc"
---
# Fifth Review Lane — Python / ROCS Producer

## Identity

- Primary: `semantic-discovery-protocol-v0.md@c8b2cc2`
- Companion: `semantic-preflight-adapter-v0.md@27481b03`
- Peer run: `scoutpeer-mrhjxgt9-e0bf8f6b`
- Mode: independent read-only producer review

## Outcome

```text
review_outcome = revise_rfc
```

An independent producer/verifier pair is not yet forced to agree byte-for-byte.

## Blocking families

1. Reserved production selector shape is absent although `unsupported_identity` requires a parseable form.
2. Corpus/effective schema literals and prepared-runtime manifest digest domain/preimage are incomplete; tool digest omission remains ambiguous.
3. Error nullability, message bound, and parseable-invalid request hashing are not formally closed.
4. `identifier` delegates to external ROCS grammar; profile/layer/root grammar is unresolved.
5. Phrase evidence cannot fit one `query_token`; field/rule validity, token-set membership, scoring clamp order, and >256 evidence behavior are incomplete.
6. Candidate/result relational invariants are missing: ordering, contiguous ranks, uniqueness, matched-token/evidence consistency, top-K and retrieval/truncation consistency.
7. Snapshot ref/root uniqueness and total ordering are incomplete.
8. Normative result example violates the required eight-key `effective_limits` schema.
9. Pack ordering, root inclusion, uniqueness, `max_bytes`, `rel_types`, and canonical envelope meaning are incomplete.
10. Python version and normalized-token canonical representation are not frozen.

Capabilities singleton arrays are otherwise closed. Recommendation: machine-readable JSON Schemas, explicit digest-omitted pseudotypes, and golden valid/invalid fixtures before another review.
