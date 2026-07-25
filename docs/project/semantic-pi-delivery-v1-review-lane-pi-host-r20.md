---
summary: "Pi host-owner exact-byte review of semantic Pi delivery v1 RFC r20."
read_when: ["Tracing Decision 71 r20 review findings."]
type: "review_lane"
status: "complete"
review_outcome: "revise_rfc"
---
# Pi host-owner lane — r20

Reviewed commit `0bafbe176195c888d985525191ab82b778251ca2`, tree `3890bbccb0be3f17e651423998e3608b84310247`, aggregate `3bf60750cc4845bf8c4635f9d24926336c07d2cf5692102af85c86dbad71553c`. Dispatch `dispatch-1784986719407` independently reproduced the fourteen-file exact-byte set and inspected immutable Pi host commit `0e773d7b0e17dacbe766e174570ab38ef619ff75` only for bounded assignment/readback seam feasibility.

The post-assignment/readback seam remains feasible and truthfully stops before provider dispatch. The complete production lineage evidence chain is not yet serializable.

## Findings

Blockers:

1. `pi.host-lineage-reap-observation.v1` is required to be published with a current read receipt before teardown, but the closed `semantic-release.authority-store-read-receipt.v1` `subject_kind` inventory omits `host_lineage_reap_observation`. Production resolver/history contexts also carry no explicit current reap-observation receipt. The recovery actor therefore cannot establish the required currentness boundary.
2. Signed `pi.host-lineage-closeout.v1` has a fixed finalizer issuer but no exact signing-purpose assignment in the closed key-purpose inventory or its own clause. Generator or implementation selection would invent authority semantics and permit purpose confusion.

Material improvements: none beyond those blockers.

Non-blocking confirmation: loaded-artifact provenance, generation/attempt identity, no provider/model-use overclaim, FD7/FD8/FD9 directionality, signed pidfd transfer, FD10 barriers, host → supervisor → controller → finalizer reap ownership, seccomp source closure, and the 25 future host obligations are otherwise coherent. This is feasibility review, not implementation proof.

## Outcome and legal next move

`revise_rfc`. Add a closed current read-receipt path for the lineage reap observation and carry it through teardown/resolver/history evidence; assign the lineage closeout one exact signing purpose and current host-owner authority closure; then freeze a new revision and rerun all five lanes.

This lane grants no ADR drafting, implementation, dogfood, publication, adoption, activation, production, recovery, or live authority.
