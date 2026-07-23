---
summary: "Pi component-owner review of semantic Pi delivery v1 RFC revision r1."
read_when:
  - "Revising or synthesizing decision 71 RFC review r1."
type: "review_memo"
status: "complete"
review_outcome: "revise_rfc"
---

# Pi component-owner review — semantic Pi delivery v1 r1

- Reviewed commit: `45b1558ee5687a7817c0fd7e40ea00b5e54c1581`
- Manifest aggregate: `f8677a1a58e8eb0a77f315ba1652cca4254b44a1c0a628b3aa02dfab327227e2`
- Dispatch: `dispatch-1784832221100`
- Outcome: `revise_rfc`

Exact-byte verification passed.

## Blockers

1. `package_distribution_digest` is not cryptographically joined to the host-observed loaded component manifest/entry. Pin the package artifact algorithm, local/npm cases, owner of each value, and substitution rejection.
2. Removing `isolatedDogfood` has no closed replacement membrane. Define the authorization schema, issuer/currentness/expiry, delivery into runtime, atomic one-shot consumption, crash/replay behavior, and how default-off permits one attempt.
3. The receipt union is incomplete: delivered-only fields are absent from the common example, complete branch key sets are unspecified, and host-witness resolution is not closed.

## Material improvements

- V1 must add no public tool, command, prompt, flag, default, or general export; product-doc reconciliation precedes code.
- Consumer/canary values are copied only from a recursively validated ROCS generation receipt and never attest repository existence, naming, consent, adoption, or activation.

## Legal next move

Revise the RFC, freeze new bytes, and rerun all required lanes. This review grants no implementation, dogfood, publication, adoption, activation, production, or live authority.
