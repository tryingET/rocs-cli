---
summary: "Pi host-owner review of semantic Pi delivery v1 RFC revision r1."
read_when:
  - "Revising or synthesizing decision 71 RFC review r1."
type: "review_memo"
status: "complete"
review_outcome: "revise_rfc"
---

# Pi host-owner review — semantic Pi delivery v1 r1

- Reviewed commit: `45b1558ee5687a7817c0fd7e40ea00b5e54c1581`
- Manifest aggregate: `f8677a1a58e8eb0a77f315ba1652cca4254b44a1c0a628b3aa02dfab327227e2`
- Dispatch: `dispatch-1784832221100-1`
- Outcome: `revise_rfc`

Exact-byte verification passed. Current Pi has a feasible post-assignment/pre-agent-run insertion seam, but the contract is not closed.

## Blockers

1. A public unkeyed self-digest does not prove host issuance. Freezing an object does not stop component reconstruction. Define independently verifiable host issuance, resolution, or redemption, or weaken the claim.
2. Loaded-artifact identity is undefined under jiti, mutable local paths, transitive imports, inline factories, and package/git installs. Pin a content-addressed immutable staging design or a narrower truthful artifact claim before ADR.
3. Define the post-application API/event, personalized receiver, handler/contribution identity, acknowledgement/error behavior, component receipt return, and exact applied-entry preimage.
4. Define generation/attempt allocation, process/restart behavior, stale checks after awaits, rollover, and replay durability. Component-local memory cannot prove single-use.
5. Enumerate exhaustive closed receipt and witness key sets; “minimum fields” is incompatible with a closed digest-bearing object.

## Material improvements

Narrow the temporal statement to “before construction or dispatch of this agent run's next provider request”; host-owned model calls may occur elsewhere.

## Legal next move

Revise and rerun exact-byte review. No implementation or authority is granted.
