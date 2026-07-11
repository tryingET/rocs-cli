---
summary: "Wave 6 local-only consumer adoption behavior coverage."
read_when:
  - "Reviewing bootstrap or generated local-gate behavior."
---

# Wave 6 local consumer coverage

Wave 6 makes the checked-in, vendored runtime the sole generated gate authority.

| Contract | Executable evidence |
|---|---|
| `ontology_repo` uses root `manifest.yaml` and `src/**`; unmanaged bytes survive and convergence is identical | `tests/test_wave6_consumer_adoption.py` |
| Required and root-layout generated wrapper and hook execute with sanitized environment, `python -I -S -B`, no uv or ambient package path | `tests/test_wave6_consumer_adoption.py` |
| `local-dev` passes `--only path`; strict profiles pass `--resolve-refs` with strict local-ref matching | generated-wrapper execution plus `tests/test_workspace_resolution.py` |
| Runtime or lock tampering fails before bundled imports | `tests/test_wave6_consumer_adoption.py` |
| Bootstrap uses one persistent external sibling `.<repo>.rocs-bootstrap.lock`, reported separately from managed paths; whole-generation publication never exchanges or unlinks its inode and creates no in-repo vendor lock | `tests/test_wave0_safety.py`; `tests/test_wave6_consumer_adoption.py` |
| GitLab pipeline and include-rewriter authority are absent | source-tree review and full test discovery |
| Wheel and sdist carry immutable `_bootstrap_assets` and install/bootstrap/verify independently without checkout discovery | isolated-build verification evidence for AK task 3726 |
| Real root-layout ontology consumer works without source mutation | disposable `git archive HEAD` dogfood evidence for AK task 3726 |

Removed interfaces are intentionally breaking: `.gitlab-ci.yml` and `rocs_cli.gitlab_ci.remove_rocs_include` have no compatibility shim. Legacy GitLab locator rejection remains as local manifest parsing safety, not remote workflow authority. `fcos_gate.LEGACY_FCOS_GATE_CANDIDATES` only detects stale downstream files for remediation; it does not execute or generate a GitLab workflow.
