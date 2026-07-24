---
summary: "Pi host-owner exact-byte review of semantic Pi delivery v1 RFC r15."
read_when: ["Tracing Decision 71 r15 review findings."]
type: "review_lane"
status: "complete"
review_outcome: "revise_rfc"
---
# Pi host-owner lane — r15

Reviewed commit `9aaaecd050261ba2cebb08d0e0469f89f46bfdbf`, aggregate `e6719438d2922f9c281f4fb12efeca310dfaab21ed2937034a27e4c639ff60a6`. `dispatch-1784866291336-1` independently reproduced the aggregate and inspected Pi host commit `0e773d7b0e17dacbe766e174570ab38ef619ff75` only for feasibility.

## Findings

Blockers:

1. Registrar identity is self-asserted rather than host-bound to the exact ExtensionAPI, loaded manifest/entry, and generation.
2. The read-only sandbox and exhaustive FD3 barrier expose no conforming durable channel for journal/transcript persistence, fsync acknowledgement, or recovery identity.
3. Host-attestation authentication inputs are absent from the exact resolver context, so a self-digested resolution remains forgeable.
4. Read-only bind plus repeated checking does not prevent same-inode mutation through a writable alias; immutable sealed staging and registrar linkage are required.

Material improvements:

- Close witness prompt-digest equations and pass an immutable/deep-frozen witness projection.
- Define UID/GID maps, `setgroups`, child pause, and exact namespace bootstrap mechanics.
- Define generation/attempt allocation, reset, rotation, and first-used values.
- Define the actual repeated redemption operation and controller-observed replay rejection.
- Remove later provider-dispatch language from the network-forbidden witness mode or assign it to a separately specified mode.

The assignment/readback seam itself is feasible, and the claim correctly stops at prompt-chain insertion.

## Outcome and legal next move

`revise_rfc`. Close the blockers and material architecture choices, then freeze and rerun all five lanes.

This lane grants no implementation, dogfood, publication, adoption, activation, live, ADR-acceptance, provider-dispatch, or production-delivery authority.
