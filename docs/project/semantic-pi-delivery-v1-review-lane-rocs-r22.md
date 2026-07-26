---
summary: "Decision 80 r22 ROCS protocol exact-byte review lane."
read_when: ["Tracing r22 strict-convergence findings."]
type: "review_lane"
status: "complete"
review_outcome: "revise_rfc"
---
# ROCS protocol lane — r22

- Frozen commit: `b834dc2e3b450483a7f0bfabf8fa88a910d9beb8`
- Fourteen-file aggregate: `4c874dbbc016b09c5e2ba7b5c17dce20a9f4133ec8e7380a6b421e534eefec4f`
- Peer run: `scoutpeer-ms1ahrlp-361b39c7`
- Outcome: `revise_rfc`

The lane independently reproduced the aggregate and exact input identities: `CaseFolding.txt` `84690`/`cdd49e55...`, `UnicodeData.txt` `1913704`/`806e9aed...`, and `CompositionExclusions.txt` `8911`/`3b019c0a...`. It reproduced exactly six non-emitting `Cs` sentinel tuples, 34,918 scalar UnicodeData sources, and a 2,979-row nontrivial normalization-source union with scalar-only mappings, exclusions, composition, and recursive output.

## Blocker

The pinned CaseFolding and CompositionExclusions files contain non-ASCII comment bytes, while the reviewed “line-oriented ASCII” requirement does not establish whether ASCII validation happens before or after raw comment stripping. Whole-line validation and comment-first validation disagree on the mandated inputs. Independent validators therefore cannot be required to converge without a new normative ordering rule.

## Legal next move

Add the exact raw-byte preprocessing order, refreeze all fourteen files, and rerun strict convergence. No packet, implementation, owner acceptance, dogfood, or production action is authorized.
