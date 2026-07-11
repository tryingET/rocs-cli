---
summary: "Wave 5 semantic transaction invariant closure and adversarial coverage."
read_when:
  - "Reviewing semantic transaction publication, recovery, or rollback guarantees."
type: "reference"
---

# Wave 5 transaction invariant coverage

| Invariant | Enforcement and evidence |
|---|---|
| Preimage authority binds bytes and exact permission mode | `transactions._check_preimages`; `test_preimage_permission_drift_fails_closed` plus stale-byte lifecycle coverage. |
| Recovery closes before new mutation | Under the ontology transaction lock, both apply and rollback close every apply journal across direct-sibling receipt roots and the ontology-bound rollback journal before staging. Journals carry self-contained byte/mode authority and recover deterministically; malformed, forged, or unknown states preserve evidence and refuse. `test_process_death_after_exchange_is_recovered_before_distinct_apply` kills a subprocess after exchange before a distinct apply; `test_apply_recovers_pending_rollback_before_distinct_mutation` proves cross-operation closure. |
| Publication is generation-atomic | A same-filesystem staged tree must pass the closed ROCS verifier and match all authority-receipt postimage byte digests and exact modes before `renameat2(RENAME_EXCHANGE)`. Existing multi-write and injected-failure tests cover compensation. |
| Receipt is proven | Apply verifies the durable receipt against the live generation immediately after receipt publication and before journal cleanup or success. Receipt forgery and post-apply drift remain fail closed. |
| Rollback authority is explicit | Rollback requires the original digest-valid transaction and applied receipt, verifies the live postimage, stages receipt-bound byte preimages with their exact modes, and exchanges a complete generation under the transaction lock. It is a mutation command authorized by possession/provision of those artifacts; it does not request a new operator approval. |

## Boundaries and breaking behavior

Receipt roots must now be direct siblings of the ontology root. This deliberate breaking constraint makes the complete journal namespace finite: under the ontology lock, apply and rollback scan the parent and every direct sibling receipt root before mutation, including journals from a receipt root or transaction different from the incoming command. The singleton rollback journal is also self-contained and included in that closure. A malformed pending journal in this namespace blocks mutation because its ontology relevance cannot be established safely. Permission-only drift now invalidates simulation/apply even when bytes are unchanged.

Rollback is generation-atomic on platforms supporting Linux `renameat2(RENAME_EXCHANGE)`, but it is not an undo of unrelated later changes: receipt verification refuses if any transaction postimage changed. Files outside declared writes are preserved and compared across recovery generations. No shell, network, model execution, or implicit approval occurs.
