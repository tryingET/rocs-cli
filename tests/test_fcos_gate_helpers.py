from __future__ import annotations

import unittest
from pathlib import Path

from rocs_cli.fcos_gate import (
    FCOS_HOOKS_README,
    default_profile_for_gate_mode,
    hook_contract_evidence,
    render_pre_push_hook,
    wrapper_workspace_contract_evidence,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class TestFcosGateHelpers(unittest.TestCase):
    def test_default_profile_for_gate_mode(self) -> None:
        self.assertEqual(default_profile_for_gate_mode("advisory"), "local-dev")
        self.assertEqual(default_profile_for_gate_mode("strict"), "main-strict")

    def test_unknown_gate_mode_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported gate mode"):
            render_pre_push_hook("inventory_only")

    def test_rendered_advisory_hook_contains_shared_contract(self) -> None:
        hook = render_pre_push_hook("advisory")

        self.assertIn('export ROCS_CI_PROFILE="${ROCS_CI_PROFILE:-local-dev}"', hook)
        self.assertIn('export ROCS_CMD="${ROCS_CMD:-uv run --project ./tools/rocs-cli python -m rocs_cli}"', hook)
        self.assertIn("bash scripts/ci/full.sh", hook)

        evidence = hook_contract_evidence(hook)
        self.assertTrue(evidence["wrapper_call_present"])
        self.assertTrue(evidence["profile_contract_present"])

    def test_rendered_strict_hook_contains_shared_contract(self) -> None:
        hook = render_pre_push_hook("strict")

        self.assertIn('export ROCS_CI_PROFILE="${ROCS_CI_PROFILE:-main-strict}"', hook)
        evidence = hook_contract_evidence(hook)
        self.assertTrue(evidence["wrapper_call_present"])
        self.assertTrue(evidence["profile_contract_present"])

    def test_comment_only_hook_markers_do_not_count(self) -> None:
        evidence = hook_contract_evidence("# ROCS_CI_PROFILE=branch-ci bash scripts/ci/full.sh\n")

        self.assertFalse(evidence["wrapper_call_present"])
        self.assertFalse(evidence["profile_contract_present"])
        self.assertEqual(evidence["lines"], [])

    def test_hook_without_profile_assignment_fails_contract(self) -> None:
        evidence = hook_contract_evidence("#!/usr/bin/env bash\nset -euo pipefail\nbash scripts/ci/full.sh\n")

        self.assertTrue(evidence["wrapper_call_present"])
        self.assertFalse(evidence["profile_contract_present"])

    def test_repo_wrapper_satisfies_workspace_contract(self) -> None:
        wrapper = (REPO_ROOT / "scripts" / "ci" / "full.sh").read_text("utf-8")
        evidence = wrapper_workspace_contract_evidence(wrapper)

        self.assertTrue(evidence["workspace_root_present"])
        self.assertTrue(evidence["workspace_ref_mode_present"])
        self.assertTrue(evidence["workspace_contract_ok"])

    def test_commented_workspace_tokens_do_not_count(self) -> None:
        wrapper = (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "# export ROCS_WORKSPACE_ROOT=\"${ROCS_WORKSPACE_ROOT:-$HOME/ai-society}\"\n"
            "# export ROCS_WORKSPACE_REF_MODE=\"${ROCS_WORKSPACE_REF_MODE:-strict}\"\n"
        )
        evidence = wrapper_workspace_contract_evidence(wrapper)

        self.assertFalse(evidence["workspace_root_present"])
        self.assertFalse(evidence["workspace_ref_mode_present"])
        self.assertFalse(evidence["workspace_contract_ok"])

    def test_hooks_readme_stays_aligned_with_wrapper_entrypoint(self) -> None:
        self.assertIn("git config core.hooksPath .githooks", FCOS_HOOKS_README)
        self.assertIn("scripts/ci/full.sh", FCOS_HOOKS_README)


if __name__ == "__main__":
    unittest.main()
