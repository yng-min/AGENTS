"""
Tests for documentation impact rendering.
"""

import unittest
from pathlib import Path
from unittest.mock import patch

from agents_tools.docs import DocumentationImpact, check_documentation, render_documentation_impacts


class DocumentationTestCase(unittest.TestCase):
    """
    Verify changed repository surfaces produce documentation candidates.
    """
    @patch("agents_tools.docs._get_diff")
    @patch("agents_tools.docs._get_changed_files")
    def test_configuration_change_targets_existing_document(
        self,
        get_changed_files,
        get_diff
    ) -> None:
        get_changed_files.return_value = [Path("config/settings.toml")]
        get_diff.return_value = ""

        with patch.object(Path, "exists", return_value=True):
            impacts = check_documentation(root=Path("."), base="main")

        self.assertTrue(any(impact.path == Path("docs/configuration.md") for impact in impacts))

    def test_render_documentation_impacts(self) -> None:
        impacts = [
            DocumentationImpact(
                path=Path("README.md"),
                reason="Callable surface changed",
                confidence="medium"
            )
        ]

        output = render_documentation_impacts(impacts=impacts)

        self.assertIn("README.md", output)
        self.assertIn("Callable surface changed", output)
