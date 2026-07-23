---
summary: "ROCS protocol review of semantic Pi delivery v1 RFC revision r1."
read_when:
  - "Revising or synthesizing decision 71 RFC review r1."
type: "review_memo"
status: "complete"
review_outcome: "revise_rfc"
---

# ROCS protocol review — semantic Pi delivery v1 r1

- Reviewed commit: `45b1558ee5687a7817c0fd7e40ea00b5e54c1581`
- Manifest aggregate: `f8677a1a58e8eb0a77f315ba1652cca4254b44a1c0a628b3aa02dfab327227e2`
- Dispatch: `dispatch-1784832221101`
- Outcome: `revise_rfc`

Exact-byte verification passed.

## Blockers

1. Receipt/witness branches are not exhaustive closed schemas; required/null/forbidden fields and equality targets are incomplete.
2. Every derived digest lacks a pinned preimage/domain, and package-to-loaded-artifact binding is absent.
3. The full attempt tuple is not present in every branch; atomic replay-state transitions, restart behavior, and bounded retention are undefined.
4. Specify a compatibility matrix and runtime dispatcher that preserves historical v0 and unchanged surrounding v0 objects while rejecting only v0 delivery at the successor boundary.
5. Pin packet manifest row encoding, path confinement, self-inclusion rule, aggregate domain, inventory rejection, exact resource limits, stable no-follow reads, deadlines, host-manifest limits, and replay-state bounds.

## Material improvements

- The generator must not import either validator's JCS/digest implementation; both validators need independent raw vectors.
- Pin the integer-only I-JSON/JCS profile and adversarial vectors in v1.
- Use deterministic embedding mechanics whose output is stable across clean checkouts and toolchains.

## Legal next move

Revise the RFC and repeat independent exact-byte review. No implementation or live authority is granted.
