---
summary: "Controlling synthesis for semantic Pi delivery v1 RFC review r1."
read_when:
  - "Determining the legal next move for decision 71 after review r1."
type: "review_synthesis"
status: "complete"
review_outcome: "revise_rfc"
---

# Review synthesis — semantic Pi delivery v1 r1

## Inputs

- Reviewed commit: `45b1558ee5687a7817c0fd7e40ea00b5e54c1581`
- Manifest aggregate: `f8677a1a58e8eb0a77f315ba1652cca4254b44a1c0a628b3aa02dfab327227e2`
- Review set: [`semantic-pi-delivery-v1-review-set-plan.md`](semantic-pi-delivery-v1-review-set-plan.md)
- Current-track memo: [`semantic-pi-delivery-v1-review-memo-r1.md`](semantic-pi-delivery-v1-review-memo-r1.md)
- Five lane artifacts and dispatches cited by that memo.

All required lanes completed against identical bytes. Every lane returned `revise_rfc`; there is no owner disagreement to adjudicate.

## Synthesis

The proposal correctly selects the real component identity, separates host observation, preserves v0, and keeps live gates closed. It is not ADR-ready because its core security and execution contracts remain under-specified:

- host issuance is forgeable as public self-digested JSON;
- package/loaded artifact/host/generation/attempt/ROCS joins are incomplete;
- receipt, witness, authorization, and replay state are not closed;
- isolated proof is conflated with protocol-valid delivery despite absent action-time owner facts;
- compatibility, packet authentication, resource limits, and embedding generation are not exact.

These are architecture-shaping blockers, not post-ADR implementation details.

## Controlling outcome

`revise_rfc`

## Legal next move

1. preserve all r1 reviews as immutable history;
2. revise the RFC to close every cross-cutting finding;
3. commit and calculate a new exact-byte manifest;
4. rerun all five lanes;
5. create a new controlling synthesis.

No ADR, implementation, dogfood, publication, adoption, activation, or live authority is granted.
