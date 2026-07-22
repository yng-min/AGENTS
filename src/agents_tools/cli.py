"""
Command-line interface for repository analysis tools.
"""

import argparse
from pathlib import Path
from typing import Sequence

from agents_tools.docs import check_documentation, render_documentation_impacts
from agents_tools.impact import analyze_impact, render_impact_report
from agents_tools.scanner import scan_project


def build_parser() -> argparse.ArgumentParser:
    """
    Build the command-line parser.
    """
    parser = argparse.ArgumentParser(prog="agents-tools")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    impact_parser = subparsers.add_parser("impact", help="Analyze a file or symbol impact surface")
    impact_parser.add_argument("target", help="File path, symbol name, or path::symbol")

    docs_parser = subparsers.add_parser("docs", help="Check documentation synchronization")
    docs_subparsers = docs_parser.add_subparsers(dest="docs_command", required=True)
    docs_check_parser = docs_subparsers.add_parser("check", help="Find documentation update candidates")
    docs_check_parser.add_argument("--base", default="main", help="Base branch or commit")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """
    Run the selected repository analysis command.
    """
    parser = build_parser()
    arguments = parser.parse_args(argv)
    root = arguments.root.resolve()

    try:
        if arguments.command == "impact":
            index = scan_project(root=root)
            report = analyze_impact(index=index, target=arguments.target)
            print(render_impact_report(report=report))
            if index.syntax_errors:
                print(f"\nUnresolved Python files: {len(index.syntax_errors)}")
            return 0

        if arguments.command == "docs" and arguments.docs_command == "check":
            impacts = check_documentation(root=root, base=arguments.base)
            print(render_documentation_impacts(impacts=impacts))
            return 0
    except (OSError, RuntimeError) as error:
        parser.error(str(error))

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
