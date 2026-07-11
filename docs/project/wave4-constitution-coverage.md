---
summary: "Wave 4 deterministic constitutional foundry and repair-market coverage."
read_when:
  - "Reviewing constitutional candidate or fleet repair proposal behavior."
---

# Wave 4 constitution coverage

Wave 4 is proposal-only. `rocs constitution validate|challenge|differential|mutate`
and `rocs repair-market` never install or activate rules, suppress findings,
certify validity, select/apply a bid, execute generated code, or mutate repository,
ontology, or fleet state. Every result states that hashing proves integrity, not
truth. Evidence is always an `unverified_claim` with a provenance locator.

| Contract | Actual test evidence |
|---|---|
| Distinct fixture schemas, global identities, `schema_conformant` / `fixtures_consistent`, and no validity certification | `tests/test_constitution.py::ConstitutionTests.test_candidate_challenge_and_positional_differential` |
| Bounded plain JSON trees, strict duplicate keys, exact bool/int comparison, and deterministic failures | `tests/test_constitution.py::ConstitutionTests.test_plain_json_exact_types_budgets_and_global_identities_fail_closed` |
| Separate exact operator acceptance, closed corpus evaluation, exact mutant packets/digests, and killed/survived/spec-ambiguous outcomes | `tests/test_constitution.py::ConstitutionTests.test_mutants_require_separate_exact_operator_acceptance_and_closed_corpus` |
| Market/metric/bid/evidence binding and evidence-neutral Pareto dominance | `tests/test_constitution.py::ConstitutionTests.test_pareto_does_not_reward_claim_count_and_binds_market` |
| Real subprocess dogfood for validate, challenge, differential, mutate, and repair-market; abbreviations, duplicate keys, nonconformance, and before/after Git snapshots | `tests/test_constitution.py::ConstitutionTests.test_real_cli_duplicate_abbreviation_nonconformance_and_no_mutation` |

Differential inputs use an exact digest-bound subject packet and bind candidate A
and B positionally. Set-like collections are sorted and unique. Mutation requires
separate canonical operator acceptance bound to the exact contract digest and
evaluates emitted mutated contracts against a closed corpus without installation.
Repair plans are closed data, bids and evidence manifests are canonical, and the
result binds the complete bid list, market digest, evidence manifest, and metric
definition/version. Evidence can annotate or gate a bid but claim count never
improves Pareto rank. No winner is selected or applied.
