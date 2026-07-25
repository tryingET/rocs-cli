---
summary: "Pi host-owner exact-byte review of semantic Pi delivery v1 RFC r19."
read_when: ["Tracing Decision 71 r19 review findings."]
type: "review_lane"
status: "complete"
review_outcome: "revise_rfc"
---
# Pi host-owner lane — r19

Reviewed commit `7ef473aec81ecc8e955d8324918f31b71dd0b3dd`, tree `96eb6037f71a5666c7b25dd19e03acc493bb279c`, aggregate `13776689613245f8ce7320a775e493fd1807f2240d53cbdab09984906733e8f7`. Dispatch `dispatch-1784981883477` read all eleven files, independently reproduced the commit/tree and aggregate, and inspected immutable Pi host commit `0e773d7b0e17dacbe766e174570ab38ef619ff75` only for bounded seam feasibility.

The post-assignment/readback seam is feasible and truthfully stops before provider dispatch. The complete witness-capable path is not yet executable.

## Findings

Blockers:

1. FD7 and FD8 credential rules are directionally impossible. `SO_PASSCRED` is enabled on both receivers, while FD7 requires every frame credential to match the finalizer PID and FD8 writer responses require no ancillary item. Broker-to-finalizer and writer-to-finalizer responses necessarily carry the broker/writer credential to an enabled receiver and therefore reject.
2. `pi.production-recovery-pidfd-transfer.v1` is described as broker-signed, but its exact object has no `statement_digest`, signing-key, algorithm, or signature fields. Its claimed `host_executable_launch` authentication cannot be serialized under the closed schema.
3. Normal terminal reap ownership is incomplete. The supervisor reaps host and controller reaps supervisor, but the finalizer only polls the controller pidfd and the broker does not explicitly reap its finalizer child. A signaled pidfd may still denote an exited zombie, so controller/finalizer absence cannot be established as claimed.

Material improvements:

- Freeze host fixture obligations for bidirectional FD7/FD8 credentials, unsigned/substituted pidfd transfer, and exited-but-unreaped controller/finalizer cases.
- Reconcile the machine requirement for separate seccomp self-test coverage with the closed thirteen-case host fixture and 115-row coverage inventory.

Architecture-shaping open questions: none beyond the mandatory repairs above.

Non-blocking confirmation: loaded-artifact provenance, generation/attempt identity, one-use redemption, durable replay closure, integration non-authority, and the no-provider-transmission claim otherwise remain coherent.

## Outcome and legal next move

`revise_rfc`. Define directional credential/ancillary matrices, add an authenticated pidfd-transfer signature closure, assign explicit normal/failure reap ownership and ordering, update frozen host coverage, then freeze and rerun all five lanes.

This lane grants no ADR drafting, implementation, dogfood, publication, adoption, activation, production delivery, or live authority.
