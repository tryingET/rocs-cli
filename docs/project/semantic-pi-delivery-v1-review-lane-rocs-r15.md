---
summary: "ROCS protocol exact-byte review of semantic Pi delivery v1 RFC r15."
read_when: ["Tracing Decision 71 r15 review findings."]
type: "review_lane"
status: "complete"
review_outcome: "revise_rfc"
---
# ROCS protocol lane — r15

Reviewed commit `9aaaecd050261ba2cebb08d0e0469f89f46bfdbf`, aggregate `e6719438d2922f9c281f4fb12efeca310dfaab21ed2937034a27e4c639ff60a6`. `dispatch-1784866291337` independently reproduced the aggregate with Python and Node.

## Findings

Blockers:

1. Canonical package/source/component provenance joins remain absent, allowing a self-consistent substituted package.
2. Host-attestation, owner-approval, owner-store, and canonical-ledger authentication evidence is absent from the closed resolver inputs, so independent validators cannot reject forged/copy authority.
3. Closed schemas still omit normative choices, including `controller_identity`, packet-manifest shape/hash encoding, deterministic dual trust-state precedence, and mandatory adversarial vectors.

Material improvements:

- Define CSPRNG uniqueness/non-reuse scope for boot/session nonces and exact attempt ordinal scope.
- Pin a deterministic dependency/import grammar and resolution algorithm.
- Pin the accepted v0 baseline manifest/aggregate used by preservation and overlay checks.
- Prevent unauthenticated suppressed/failed receipt claims from masquerading as component-issued evidence.

The JCS profile, domain separation, acyclic witness/redemption construction, provider-transmission separation, and embedding recipe are otherwise directionally deterministic.

## Outcome and legal next move

`revise_rfc`. Close provenance, authenticated authority inputs, remaining schemas/precedence, nonce/import/baseline rules, and adversarial vectors; then freeze and rerun all five lanes.

This lane grants no implementation, dogfood, integration run, publication, adoption, activation, live, ADR-drafting, or production authority.
