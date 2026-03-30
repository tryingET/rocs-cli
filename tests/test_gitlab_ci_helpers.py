from __future__ import annotations

import unittest

from rocs_cli.gitlab_ci import remove_rocs_include


class TestGitlabCiHelpers(unittest.TestCase):
    def test_remove_rocs_include_leaves_non_rocs_include_unchanged(self) -> None:
        original = "include:\n  local: 'gitlab/ci/existing.yml'\nstages:\n  - test\n"
        self.assertEqual(remove_rocs_include(original), original)

    def test_remove_rocs_include_removes_reference_tag_entry_without_roundtrip_loss(self) -> None:
        original = "\n".join(
            [
                "include:",
                "  - local: 'gitlab/ci/rocs.yml'",
                "job:",
                "  rules: !reference [.shared, rules]",
                ".shared:",
                "  rules:",
                "    - if: $CI_PIPELINE_SOURCE",
                "",
            ]
        )

        updated = remove_rocs_include(original)

        self.assertIsNotNone(updated)
        self.assertNotIn("gitlab/ci/rocs.yml", updated)
        self.assertIn("!reference [.shared, rules]", updated)

    def test_remove_rocs_include_removes_flow_style_entry(self) -> None:
        original = "\n".join(
            [
                "include: ['gitlab/ci/rocs.yml', 'gitlab/ci/keep.yml']",
                "job:",
                "  script:",
                "    - echo ok",
                "",
            ]
        )

        updated = remove_rocs_include(original)

        self.assertEqual(updated, "include:\n- gitlab/ci/keep.yml\njob:\n  script:\n  - echo ok\n")

    def test_remove_rocs_include_removes_inline_mapping_entry(self) -> None:
        original = "\n".join(
            [
                "include: {local: 'gitlab/ci/rocs.yml'}",
                "job:",
                "  script:",
                "    - echo ok",
                "",
            ]
        )

        updated = remove_rocs_include(original)

        self.assertEqual(updated, "job:\n  script:\n  - echo ok\n")

    def test_remove_rocs_include_removes_multiline_entry_atomically(self) -> None:
        original = "\n".join(
            [
                "include:",
                "  - local: 'gitlab/ci/rocs.yml'",
                "    rules:",
                "      - if: $CI_PIPELINE_SOURCE",
                "  - local: 'gitlab/ci/keep.yml'",
                "job:",
                "  rules: !reference [.shared, rules]",
                ".shared:",
                "  rules:",
                "    - if: $CI_PIPELINE_SOURCE",
                "",
            ]
        )

        updated = remove_rocs_include(original)

        self.assertIsNotNone(updated)
        self.assertNotIn("gitlab/ci/rocs.yml", updated)
        self.assertIn("gitlab/ci/keep.yml", updated)
        self.assertIn("!reference [.shared, rules]", updated)
        self.assertNotIn("    rules:\n      - if: $CI_PIPELINE_SOURCE\n  - local: 'gitlab/ci/keep.yml'", updated)

    def test_remove_rocs_include_returns_none_when_only_include_remains(self) -> None:
        self.assertIsNone(remove_rocs_include("include:\n  - local: 'gitlab/ci/rocs.yml'\n"))

    def test_remove_rocs_include_raises_on_invalid_non_mapping_yaml(self) -> None:
        with self.assertRaisesRegex(ValueError, "root must be a mapping"):
            remove_rocs_include("- gitlab/ci/rocs.yml\n")


if __name__ == "__main__":
    unittest.main()
