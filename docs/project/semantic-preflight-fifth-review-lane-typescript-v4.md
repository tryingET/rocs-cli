---
summary: "Decision:52 fifth bounded TypeScript/Pi independent verifier schema review lane."
read_when: ["Checking decision:52 fifth-review verifier findings."]
type: "review_memo"
decision_id: 52
review_outcome: "revise_rfc"
---
# Fifth Review Lane — TypeScript / Pi Verifier

## Identity

- Primary: `semantic-discovery-protocol-v0.md@c8b2cc2`
- Companion: `semantic-preflight-adapter-v0.md@27481b03`
- Peer run: `scoutpeer-mrhjxgtj-0f6f6682`
- Mode: independent read-only verifier review

## Outcome

```text
review_outcome = revise_rfc
```

A TypeScript verifier cannot implement complete byte-identical validation from the reviewed RFCs alone.

## Concrete blockers

1. `identifier` delegates to an unstated external grammar.
2. Corpus/effective schema literals are absent.
3. Result validation refers to `limits.candidates` although the result carries `effective_limits`.
4. The normative result example emits invalid empty `effective_limits`.
5. Global non-nullability conflicts with nullable error request digest; error message lacks a closed bound.
6. Digest-inclusive byte accounting says the digest string is 72 bytes, but it is 71 UTF-8 bytes.
7. Pi renders evidence strings while ROCS emits evidence objects; projection, ordering, and label-validation wording are not closed.

Result/pack digest omission is otherwise explicit; major enums, ranges, and array bounds are substantially improved.
