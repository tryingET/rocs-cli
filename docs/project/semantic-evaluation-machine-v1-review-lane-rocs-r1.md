---
summary: "ROCS constructibility lane for Decision 106 r1."
read_when:
  - "Reviewing Decision 106 strict convergence."
type: "review_lane"
status: "complete"
decision_id: 106
review_outcome: "reject_current_direction"
---
# Decision 106 r1 — ROCS constructibility lane

- Review receipt: `dispatch-1785751414341`
- Frozen commit: `c53a16a14562e1ed69ba4f49c171e35b62a2956f`
- Frozen tree: `bb3f3b67fd58a5408ff78eae45fdbdf02e5bdf1f`
- Four-file aggregate: `541729d1904bdc424daa66f7fbb438b157bf9123566daabbebdf0b9ba71dbda4`
- External projection: `1810` bytes / `43cb523b3787726956f331ea0917fd55757cf317a13815cd6f0f97c8b9eb7206`
- External schema: `8227` bytes / `d42569781d23c625627d92a9f37ea9c26211c92c403b0dcdb45b0360c386c532`

All exact identities reproduced from frozen Git objects. The lane found no blocker or material improvement in the rejection packet.

A semantic machine is not constructible from current inputs: no semantic-owner policy operand, subject preimages, read authority, typed digest/preimage joins, or generic authenticated producer eligibility exists. Exact-byte hashing establishes identity; JSON Schema establishes shape; neither establishes a semantic verdict. An observed return is not a semantic pass.

## Outcome

`reject_current_direction`

## Legal next move

Feed this immutable lane into complete four-lane synthesis. Record no ADR or implementation authority, keep Decision 107 blocked, and require a new decision for any future owner-supplied policy/subject contract.
