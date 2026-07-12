---
summary: "Decision:53 lane A review of semantic-owner authority, compatibility, trust, publication, and rollback."
read_when:
  - "Revising or synthesizing decision:53 review."
type: "review_memo"
status: "complete"
review_outcome: "revise_rfc"
---
# Decision 53 Review — Lane A: Semantic Owner and Publication

## Outcome

`revise_rfc`

The capsule/intent/receipt split is sound in principle, but owner authority, coordinate uniqueness, compatibility, trust, publication, lineage, and rollback are underspecified enough for divergent implementations or consumer self-certification.

## P0 findings

1. **Issuance authority is undefined.** Define namespace authority, immutable owner-policy revision and owner set, approval predicate, exact source and candidate-digest approval, and the boundary that ROCS builds/verifies but cannot issue.
2. **Coordinate grammar and uniqueness are open.** The illustrative `X.Y.Z+sha256:<digest>` is not valid closed SemVer grammar. Use a closed object or normative ASCII grammar. Permanently bind `(namespace, semantic_version)` to one digest; conflicting reuse fails closed and identical replay is idempotent.
3. **Source and capsule identities are conflated.** Separate semantic payload, capsule, owner publication, and tool identities. Define repository/source root, complete path/mode/symlink manifest, generated material, clean committed source, digest domains, and self-digest omissions.
4. **Compatibility policy is not implementable.** Require a versioned owner-approved compatibility policy digest, exhaustive change categories, SemVer consequences, machine conditions, fail-closed `unknown`, owner override rules, deprecation/removal transitions, permanent tombstones, and no ID reuse.
5. **Unsigned local trust is circular.** Define an external owner-controlled local trust root, immutable publication-ledger revision, owner publication record, capsule chain, bootstrap/update authority, anti-rollback, revocation/withdrawal, rotation, offline behavior, and threat limits.
6. **Publication and predecessor lineage are not atomic.** Define a namespace publication ledger and linearization point, exact predecessor semantics, compare-and-swap publication, crash recovery, idempotency, fork/conflict rejection, withdrawal without history rewrite, and immutable replay.
7. **Rollback readiness is asserted rather than proven.** Require previously materialized predecessor/no-prior fallback, owner and consumer rollback receipts, independent runtime rollback, and evidence that rollback remains available if the active runtime is broken.

## Required revision posture

The ontology owner must adopt the issuance and compatibility policy on its own surface before production publication. The dirty `core/ontology-kernel` worktree is not clean release evidence and was not mutated.
