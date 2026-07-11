---
summary: "Wave 7 executable authority and filesystem-effects contract schema and coverage."
read_when:
  - "Changing a public CLI operation or its filesystem writes"
---

# Wave 7 effects contract

`rocs contracts` schema 3 is an intentional alpha break. It removes `mutates`
without a compatibility field or shim. `src/rocs_cli/contracts.py` is the single
registry for every parser operation and exposes the pure `evaluate_effects()`
function. Evaluation takes parsed argument values and exactly two explicit
runtime facts: whether the index cache is enabled and whether the repository
passes the exact authority-receipt eligibility check (including unambiguous manifest resolution).

The closed conditions are `always`, exact `argument`, selected `mode`,
`path-output` (present and not stdout `-`), `runtime-feature`, and
`authority-receipt-enabled`. Effects are `none`, caller-selected or managed `artifact`,
`cache`, bounded `repository`, caller-selected `fleet`, and `ontology`.
Caller-selected graph and fleet destinations are artifacts; the declaration does
not claim they are contained by a repository.

Notable resolutions are: fleet run mutates fleet state only in `apply` mode;
normalize and check-inverses mutate ontology only with `--apply` and `--fix`;
cleanup removes managed artifacts only when not a dry run; validate emits an
authority receipt only when the runtime's exact receipt-eligibility predicate passes;
benchmark declares its temporary generated-repository writes as artifacts; and indexed
ontology readers declare cache writes only when `ROCS_INDEX_CACHE` remains
enabled (including the inverse semantics of `--no-index-cache`). Every operation
declares exits 0, 1, and 2 because handler results, the global exception boundary,
and argparse rejection are observable CLI outcomes.

## Executable coverage

`tests/test_wave1_contracts.py` enforces exact parser-operation parity, detached
canonical emission, no `mutates` field, closed rule shapes, parser destinations
and mode choices, and generic evaluation of every condition class. Its disposable
resolve matrix proves no default repository write and the exact managed artifact
created by `--write-dist`. Existing focused suites remain the behavioral evidence
for proposal/constitution none and artifact-only behavior, fleet audit/patch/apply,
normalize check/apply, inverse fixing, cleanup dry-run/apply, validation receipts,
transaction apply/rollback authority, cache enable/disable, and parser/handler
failures.

Coverage limit: effects include temporary writes even when a command cleans them
before returning, and declarations classify filesystem domains rather than exact filenames. Existing family tests prove those filenames and containment where the
CLI owns the path; caller-selected output paths intentionally have no repository
containment claim. OS metadata and Python bytecode are outside the contract.
