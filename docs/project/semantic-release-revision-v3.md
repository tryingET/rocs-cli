---
summary: "Decision:53 semantic-release revision v3 final-invariant closure attempt and validation record."
read_when: ["Reviewing semantic-release revision v3 or its remaining blockers."]
type: "revision_note"
status: "reviewed"
rfc_revision: "semantic-release-revision-v3"
review_outcome: "revise_rfc"
---
# Semantic Release Revision v3

## Objective

Close the finite invariant set from [`semantic-release-rereview2-synthesis-v2.md`](semantic-release-rereview2-synthesis-v2.md) without authorizing implementation or production behavior.

## Implemented

- typed trust actions, threshold checks, rotation/revocation revisions, and transition fixtures;
- expanded compatibility conditions, overrides, lifecycle/tombstone checks, and fixtures;
- acyclic publication transaction/journal/result-head/marker shapes and recovery cases;
- stronger capsule projection/archive linkage;
- expanded rollback targets, stages, revalidation, typed heads, partial/failure fixtures;
- activation current-head, coordinate, runtime, revocation, and supersession checks;
- canonical AK store-head/currentness fields;
- raw-token-aware duplicate-key/numeric I-JSON parsing and UTC calendar checks in Python and Node;
- independent Node-derived domain/omission/order checks;
- larger positive/negative corpus.

## Validation

- 37 closed protocol types;
- 64 canonical object preimages and 2 raw preimages;
- 28 digest links;
- 117 differential cases: 42 accepted transitions and 75 expected rejections;
- 7 raw JSON lexical cases;
- Python token-aware validator: PASS;
- independent Node token-aware validator: PASS;
- docs strict and `git diff --check`: PASS.

## Fresh review disposition

Strict rereview remains `revise_rfc`. Remaining issues include complete archive/no-extra equality, supplied-object/current-head bindings, raw Node object safety and UTF-8 ordering, canonical first-consumer task contracts, exact owner policy/set/rotation bindings, compatibility override/tombstone monotonicity, publication prior-status/journal/recovery bindings, and stronger rollback availability/history causality.

No ADR, publication, activation, default, fleet, ontology, or implementation authority follows from this revision.
