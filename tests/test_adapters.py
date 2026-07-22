"""
Tests for optional analysis adapter behavior.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents_tools.adapters import AdapterSelection, enrich_project
from agents_tools.models import AdapterState, ProjectIndex


class AdapterTestCase(unittest.TestCase):
    """
    Verify optional integrations never become mandatory for core analysis.
    """
    def test_empty_selection_keeps_core_index_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            index = ProjectIndex(root=Path(directory))

            result = enrich_project(index=index, selection=AdapterSelection(names=()))

            self.assertIs(result, index)
            self.assertEqual(result.adapter_reports, [])

    @patch("agents_tools.adapters.shutil.which", return_value=None)
    def test_missing_cli_adapter_is_reported_without_failure(self, _: object) -> None:
        with tempfile.TemporaryDirectory() as directory:
            index = ProjectIndex(root=Path(directory))

            result = enrich_project(
                index=index,
                selection=AdapterSelection(names=("pyright", "semgrep"))
            )

            self.assertEqual(len(result.adapter_reports), 2)
            self.assertTrue(
                all(report.state == AdapterState.UNAVAILABLE for report in result.adapter_reports)
            )
