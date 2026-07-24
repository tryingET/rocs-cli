---
summary: "Governance, security, and operations exact-byte review of semantic Pi delivery v1 RFC r15."
read_when: ["Tracing Decision 71 r15 review findings."]
type: "review_lane"
status: "complete"
review_outcome: "revise_rfc"
---
# Governance/security/operations lane — r15

Reviewed commit `9aaaecd050261ba2cebb08d0e0469f89f46bfdbf`, aggregate `e6719438d2922f9c281f4fb12efeca310dfaab21ed2937034a27e4c639ff60a6`. `dispatch-1784866291338` independently reproduced the aggregate.

## Findings

Blockers:

1. The closed host/component protocol transports no authorization-envelope digest to the component that must include it in the acknowledgement.
2. The authorization request omits the exact generation, input/disposable filesystem, subject kind, and `host_integration_only` mode, allowing operation substitution.
3. Integration mode does not reject a delivered receipt before journal/redemption despite `production_authorized=false`.
4. Owner and Decision 71 revocation/currentness are not re-resolved and evidenced at claim, pre-launch/witness, and terminal proof.
5. Integration proof omits canonical terminal store-head resolution, acquisition pin, and current owner-store receipt, allowing copied-ledger replay.
6. Crash/rollback semantics name no lawful finalizer and provide no cancellation/revocation transition for available authorization.

Identity split, no alias, default-off posture, and live blockers are otherwise directionally correct.

## Outcome and legal next move

`revise_rfc`. Close authorization transport and operation binding, acknowledgement-only enforcement, action-time currentness, canonical proof resolution, and abandoned/rollback lifecycle; then freeze and rerun all lanes.

This lane grants no implementation, dogfood, publication, adoption, activation, live, ADR-drafting, or production authority.
