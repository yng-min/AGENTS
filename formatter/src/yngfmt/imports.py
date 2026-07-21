"""
Project-aware import sorting and checking.
"""

from __future__ import annotations

import ast
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True, slots=True)
class ImportConfig:
    """
    Configure project-aware import classification.
    """
    first_party: tuple[str, ...] = ()
    language_segment: str = "language"
    config_segment: str = "config"


@dataclass(frozen=True, slots=True)
class ImportRecord:
    """
    Represent one top-level import statement and its source text.
    """
    node: ast.Import | ast.ImportFrom
    text: str
    root: str
    module: str
    depth: int
    kind: int
    category: int
    segment: str
    original_index: int


@dataclass(frozen=True, slots=True)
class ImportIssue:
    """
    Describe an import ordering violation.
    """
    line: int
    column: int
    code: str
    message: str


def find_pyproject(start: Path) -> Path | None:
    """
    Find the nearest pyproject.toml from a file or directory.
    """
    current = start if start.is_dir() else start.parent
    for directory in (current, *current.parents):
        candidate = directory / "pyproject.toml"
        if candidate.is_file():
            return candidate
    return None


def load_import_config(pyproject_path: Path | None) -> ImportConfig:
    """
    Load import settings from pyproject.toml.
    """
    if pyproject_path is None or not pyproject_path.is_file():
        return ImportConfig()

    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    settings = data.get("tool", {}).get("yngfmt", {}).get("imports", {})
    first_party = settings.get("first-party", ())
    if isinstance(first_party, str):
        first_party = (first_party,)

    return ImportConfig(
        first_party=tuple(first_party),
        language_segment=settings.get("language-segment", "language"),
        config_segment=settings.get("config-segment", "config")
    )


def _module_name(node: ast.Import | ast.ImportFrom) -> str:
    if isinstance(node, ast.ImportFrom):
        return node.module or ""
    return node.names[0].name


def _root_name(node: ast.Import | ast.ImportFrom) -> str:
    module = _module_name(node)
    if isinstance(node, ast.ImportFrom) and node.level:
        return ""
    return module.split(".")[0]


def _segment_name(node: ast.Import | ast.ImportFrom, config: ImportConfig) -> str:
    module = _module_name(node)
    parts = [part for part in module.split(".") if part]

    if isinstance(node, ast.ImportFrom) and node.level:
        return parts[0] if parts else ""
    if not parts or parts[0] not in config.first_party:
        return ""
    return parts[1] if len(parts) > 1 else ""


def _category(node: ast.Import | ast.ImportFrom, config: ImportConfig) -> int:
    if isinstance(node, ast.ImportFrom) and node.module == "__future__":
        return 0
    if isinstance(node, ast.ImportFrom) and node.level:
        return 3

    root = _root_name(node)
    if root in sys.stdlib_module_names:
        return 1
    if root in config.first_party:
        return 3
    return 2


def _kind(node: ast.Import | ast.ImportFrom) -> int:
    return 0 if isinstance(node, ast.ImportFrom) else 1


def _depth(node: ast.Import | ast.ImportFrom) -> int:
    module = _module_name(node)
    return len([part for part in module.split(".") if part])


def _segment_order(segment: str, config: ImportConfig) -> tuple[int, str]:
    if segment == config.language_segment:
        return 0, ""
    if segment == config.config_segment:
        return 2, ""
    return 1, segment.lower()


def _sort_key(record: ImportRecord, config: ImportConfig) -> tuple[object, ...]:
    segment_order = _segment_order(record.segment, config)
    return (
        record.category,
        segment_order if record.category == 3 else (0, ""),
        record.kind,
        record.root.lower(),
        record.depth,
        record.module.lower(),
        record.text.lower(),
        record.original_index
    )


def _top_level_import_nodes(tree: ast.Module) -> list[ast.Import | ast.ImportFrom]:
    nodes: list[ast.Import | ast.ImportFrom] = []
    body = tree.body
    start_index = 0

    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        start_index = 1

    for node in body[start_index:]:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            nodes.append(node)
            continue
        break
    return nodes


def _attached_start(lines: Sequence[str], start_line: int, lower_bound: int) -> int:
    current = start_line
    while current > lower_bound:
        previous = lines[current - 2]
        if not previous.lstrip().startswith("#"):
            break
        current -= 1
    return current


def _records(
    source: str,
    nodes: Sequence[ast.Import | ast.ImportFrom],
    config: ImportConfig
) -> tuple[list[ImportRecord], int, int]:
    lines = source.splitlines(keepends=True)
    records: list[ImportRecord] = []
    previous_end = 1

    for index, node in enumerate(nodes):
        start_line = _attached_start(lines, node.lineno, previous_end)
        end_line = node.end_lineno or node.lineno
        text = "".join(lines[start_line - 1:end_line]).strip("\n")
        records.append(
            ImportRecord(
                node=node,
                text=text,
                root=_root_name(node),
                module=_module_name(node),
                depth=_depth(node),
                kind=_kind(node),
                category=_category(node, config),
                segment=_segment_name(node, config),
                original_index=index
            )
        )
        previous_end = end_line + 1

    first_line = _attached_start(lines, nodes[0].lineno, 1)
    last_line = nodes[-1].end_lineno or nodes[-1].lineno
    return records, first_line, last_line


def _separator(
    previous: ImportRecord,
    current: ImportRecord,
    config: ImportConfig
) -> str:
    if previous.category != current.category:
        return "\n\n"
    if current.category != 3 or previous.segment == current.segment:
        return "\n"
    if current.segment == config.config_segment:
        return "\n\n\n"
    return "\n\n"


def _render(records: Sequence[ImportRecord], config: ImportConfig) -> str:
    if not records:
        return ""

    parts = [records[0].text]
    for previous, current in zip(records, records[1:]):
        parts.append(_separator(previous, current, config))
        parts.append(current.text)
    return "".join(parts)


def sort_imports(source: str, config: ImportConfig = ImportConfig()) -> str:
    """
    Sort the leading top-level import section according to the style guide.
    """
    if "# yngfmt: keep-imports" in source or "# yngfmt: off" in source:
        return source

    tree = ast.parse(source)
    nodes = _top_level_import_nodes(tree)
    if not nodes:
        return source

    records, first_line, last_line = _records(source, nodes, config)
    sorted_records = sorted(records, key=lambda record: _sort_key(record, config))
    rendered = _render(sorted_records, config)

    lines = source.splitlines(keepends=True)
    before = "".join(lines[:first_line - 1])
    after = "".join(lines[last_line:]).lstrip("\n")
    suffix = "\n\n" if after else "\n"
    return f"{before}{rendered}{suffix}{after}"


def check_imports(
    source: str,
    config: ImportConfig = ImportConfig()
) -> list[ImportIssue]:
    """
    Return one diagnostic when the import section differs from canonical output.
    """
    try:
        formatted = sort_imports(source=source, config=config)
        tree = ast.parse(source)
    except SyntaxError:
        return []

    if formatted == source:
        return []

    nodes = _top_level_import_nodes(tree)
    line = nodes[0].lineno if nodes else 1
    return [
        ImportIssue(
            line=line,
            column=1,
            code="YNG400",
            message="import section does not match project import ordering rules"
        )
    ]
