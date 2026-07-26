---
summary: "Decision 80 r22 Pi component-owner exact-byte review lane."
read_when: ["Tracing r22 strict-convergence findings."]
type: "review_lane"
status: "complete"
review_outcome: "revise_rfc"
---
# Pi component-owner lane — r22

- Frozen commit: `b834dc2e3b450483a7f0bfabf8fa88a910d9beb8`
- Fourteen-file aggregate: `4c874dbbc016b09c5e2ba7b5c17dce20a9f4133ec8e7380a6b421e534eefec4f`
- Peer run: `scoutpeer-ms1ahrl5-2047db50`
- Outcome: `revise_rfc`

The lane independently reproduced the aggregate, all three pinned Unicode input hashes, and the exact six `UnicodeData.txt` `Cs` sentinel rows. Component identity, package identity, fixed issuer, constructor-authority removal, host-private witnessing, and component issuance semantics were otherwise unchanged.

## Blocker

The validation annex says parsing is “line-oriented ASCII” before specifying per-format comment removal, but the exact pinned `CaseFolding.txt` contains six non-ASCII UTF-8 bytes in comment text and `CompositionExclusions.txt` contains four. Whole-line ASCII validation rejects the pinned sources; raw-byte `#` truncation before ASCII syntax validation accepts them. R22 does not fix the order, so Python and Node can lawfully diverge or one can reject the mandated inputs. Implementation inference is forbidden.

## Legal next move

Specify exact raw-byte preprocessing—reject CR, split on LF, remove bytes from the first ASCII `#`, then require the retained syntax bytes to be ASCII—freeze a new review set, and rerun every lane. This review grants no implementation, dogfood, live, or production authority.
