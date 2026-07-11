---
summary: "Wave 1 migration map from deleted script tests to package and CLI contract coverage."
read_when:
  - "Reviewing the Wave 1 script-to-package migration or deleted script tests."
type: "reference"
---

# Wave 1 behavior-coverage migration map

Wave 1 deleted five script-focused test modules when their entrypoints moved behind the package CLI. The previously reported **173 was a total-suite test count, not a count of deleted tests**. Counting `test*` methods in the deleted files at `HEAD` gives **71 methods**: audit fleet 20, bootstrap 21, remediation batch 11, nightly fleet 11, and vendor 8. Those counts do not imply one-for-one replacement, and deletion itself is not evidence of coverage.

The maintained replacement gates are primarily `tests/test_wave0_safety.py`, `tests/test_wave1_contracts.py`, `tests/test_cli.py`, and the exact parser/README gates. The full suite's count can change as tests are split or consolidated; closeout must report the count emitted by the actual run rather than reusing 173.

| Deleted test surface | Maintained observable-contract coverage | Explicit limit |
|---|---|---|
| `test_audit_fleet_script.py` | `test_fleet_observe_plan_and_boundary_behaviors` checks deterministic observation, pass/drift status, planning, and workspace escape. `test_fleet_report_only_output_malformed_apply_and_run_outcomes` checks report-only exit behavior, Markdown output, malformed policy rejection, dry-run apply, and audit-only run results. Existing FCOS helper tests retain manifest/hook/wrapper parsing boundaries. | Deleted script formatting, helper call structure, and internal assembly are not covered. |
| `test_bootstrap_repo_script.py` | `test_bootstrap_fresh_rerun_dry_run_and_class_behavior` exercises fresh and converge/rerun behavior, no-mutation dry-run, and all three closed repository classes. `test_wave0_safety.py` checks transactional rollback. Parser exactness checks the public commands and class choices. | Private shell/YAML editing mechanics are retired; preservation is asserted only through observable tree convergence. |
| `test_open_remediation_batch_script.py` | Fleet observe→plan drift is exercised, while the fleet outcome test covers package `apply` dry-run. The exact parser contract keeps `fleet.plan`, `fleet.apply`, and `fleet.run` closed and discoverable. | Old batch-directory naming, issue text, subprocess choreography, and cleanup internals are retired. There is no claim of one-for-one batch-script replacement. |
| `test_run_fleet_audit_nightly_script.py` | `test_scheduler_assets_parse_to_closed_fleet_run_contract` parses cron and systemd command lines and requires the `fleet run` workspace/policy contract. The fleet outcome test checks run result shape and exit outcome. | Runtime-manager selection, logging implementation, and deleted wrapper subprocess details are retired. |
| `test_vendor_to_script.py` | `test_vendor_dry_run_version_and_target_boundaries` checks no-write dry-run, explicit reported version, and source-tree target rejection. Artifact tests check unexpected/special-file rejection and execute verify/doctor/validate/build/version in an isolated consumer. | Private wrapper argument plumbing and source-descendant implementation details are retired where the package boundary supersedes them. |

## Intentionally retired implementation-only assertions

The following specified deleted wrappers rather than maintained public behavior and are not claimed as replacement coverage:

- executability or presence of the deleted bootstrap, remediation, nightly-shell, and vendor scripts;
- the nightly wrapper's selection of a repo-managed Python runtime;
- subprocess call graphs between old audit, remediation, bootstrap, and vendor scripts;
- script-private temporary names, batch-directory cleanup mechanics, JSON quoting, and intermediate files;
- exact YAML round-trip implementation details, beyond observable bootstrap preservation and convergence;
- wrapper-specific version override plumbing, beyond the package vendor result and release commands.

Any future retirement must name a maintained replacement test or classify the assertion here without inflating total-suite counts into deleted-method counts.
