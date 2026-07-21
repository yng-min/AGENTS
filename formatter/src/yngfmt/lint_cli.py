"""
Command-line interface for the style guide linter.
"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import Path

from yngfmt.linter import iter_python_files, lint_path


def build_parser() -> ArgumentParser:
    """
    Build the command-line parser.
    """
    parser = ArgumentParser(prog="ynglint")
    parser.add_argument("paths", nargs="+", type=Path)
    return parser


def main() -> int:
    """
    Run the linter and return a process exit code.
    """
    arguments: Namespace = build_parser().parse_args()
    diagnostics = []
    for path in iter_python_files(paths=arguments.paths):
        diagnostics.extend(lint_path(path=path))

    for diagnostic in diagnostics:
        print(diagnostic.render())
    return 1 if diagnostics else 0
