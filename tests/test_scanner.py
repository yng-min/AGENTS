"""
Tests for Python project scanning and impact analysis.
"""

import tempfile
import unittest
from pathlib import Path

from agents_tools.impact import analyze_impact
from agents_tools.models import Confidence
from agents_tools.scanner import scan_project


class ScannerTestCase(unittest.TestCase):
    """
    Verify definitions and references are collected with evidence levels.
    """
    def test_scan_and_analyze_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "app"
            package.mkdir()
            (package / "service.py").write_text(
                "def process(value: str) -> str:\n"
                "    return value\n",
                encoding="utf-8"
            )
            (package / "handler.py").write_text(
                "from app.service import process\n\n"
                "def handle() -> str:\n"
                "    return process(value=\"test\")\n",
                encoding="utf-8"
            )

            index = scan_project(root=root)
            report = analyze_impact(index=index, target="process")

            self.assertEqual(len(report.symbols), 1)
            self.assertTrue(any(reference.location.path == Path("app/handler.py") for reference in report.references))
            self.assertTrue(any(reference.confidence == Confidence.CONFIRMED for reference in report.references))

    def test_syntax_error_is_reported_without_stopping_scan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "valid.py").write_text("value = 1\n", encoding="utf-8")
            (root / "invalid.py").write_text("def broken(:\n", encoding="utf-8")

            index = scan_project(root=root)

            self.assertIn(Path("invalid.py"), index.syntax_errors)
