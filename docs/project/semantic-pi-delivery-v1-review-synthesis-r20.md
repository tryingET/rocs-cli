---
summary: "Controlling strict-convergence synthesis for semantic Pi delivery v1 r20."
read_when: ["Tracing Decision 71 r20 outcome and legal next move."]
type: "review_synthesis"
status: "complete"
review_outcome: "revise_rfc"
---
# Decision 71 r20 — controlling synthesis

All five required exact-byte lanes completed on commit `0bafbe176195c888d985525191ab82b778251ca2`, tree `3890bbccb0be3f17e651423998e3608b84310247`, aggregate `3bf60750cc4845bf8c4635f9d24926336c07d2cf5692102af85c86dbad71553c`.

Component, ROCS protocol, semantic-owner, and governance/security/operations lanes returned `ready_for_adr`. Pi host returned `revise_rfc`. Strict convergence does not average or outvote blockers. The controlling outcome is `revise_rfc`.

## Mandatory revision set

1. Add `host_lineage_reap_observation` to the closed authority-store read-receipt subject inventory, require the broker's current receipt for the exact `pi.host-lineage-reap-observation.v1`, and carry that receipt through the production teardown object and production resolver/history evidence so currentness is independently serializable.
2. Assign `pi.host-lineage-closeout.v1` one exact signing purpose from a reviewed key-purpose closure and require the matching current host-owner control evidence; neither generator nor implementation may choose the purpose.

## Outcome and legal next move

`revise_rfc`.

The next legal move is a new RFC revision closing both mandatory items, followed by a new immutable freeze, five exact-byte lane reviews, and controlling synthesis. ADR drafting and every implementation, dogfood, publication, adoption, activation, production, recovery, and live action remain unauthorized.

Task `4127`, ontology candidate `0d53ce3`, production defaults, and live acquisition remain deferred.
