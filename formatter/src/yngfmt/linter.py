"""
Style guide linter engine.
"""

from __future__ import annotations

import ast
import io
import re
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


_SNAKE_CASE_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")
_PASCAL_CASE_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]*$")
_BOOLEAN_PREFIXES = ("is_", "has_", "can_", "should_")


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """
    Describe one style guide violation.
    """
    path: Path
    line: int
    column: int
    code: str
    message: str

    def render(self) -> str:
        return f"{self.path}:{self.line}:{self.column}: {self.code} {self.message}"


class StyleGuideVisitor(ast.NodeVisitor):
    """
    Check syntax-aware style guide rules.
    """
    def __init__(self, path: Path) -> None:
        self.path: Path = path
        self.diagnostics: list[Diagnostic] = []

    def add(self, node: ast.AST, code: str, message: str) -> None:
        self.diagnostics.append(
            Diagnostic(
                path=self.path,
                line=getattr(node, "lineno", 1),
                column=getattr(node, "col_offset", 0) + 1,
                code=code,
                message=message
            )
        )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if not _PASCAL_CASE_PATTERN.fullmatch(node.name):
            self.add(node, "YNG201", "class name must use PascalCase")

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function(node)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if (
            isinstance(node.target, ast.Name)
            and isinstance(node.annotation, ast.Name)
            and node.annotation.id == "bool"
            and not node.target.id.startswith(_BOOLEAN_PREFIXES)
        ):
            self.add(
                node,
                "YNG203",
                "boolean variable should use is_/has_/can_/should_ prefix"
            )

        self.generic_visit(node)

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if not _SNAKE_CASE_PATTERN.fullmatch(node.name):
            self.add(node, "YNG202", "function and method names must use snake_case")

        arguments: list[ast.arg] = [
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs
        ]
        for argument in arguments:
            if argument.arg in {"self", "cls"}:
                continue
            if argument.annotation is None:
                self.add(argument, "YNG301", "parameter type annotation is missing")

        if node.args.vararg is not None and node.args.vararg.annotation is None:
            self.add(node.args.vararg, "YNG301", "*args type annotation is missing")
        if node.args.kwarg is not None and node.args.kwarg.annotation is None:
            self.add(node.args.kwarg, "YNG301", "**kwargs type annotation is missing")
        if node.returns is None:
            self.add(node, "YNG302", "return type annotation is missing")


def _string_prefix_and_quote(token_value: str) -> tuple[str, str] | None:
    match = re.match(r"(?i)^([rubf]*)(\"\"\"|'''|\"|')", token_value)
    if match is None:
        return None
    return match.group(1), match.group(2)


def _docstring_positions(tree: ast.AST) -> set[tuple[int, int]]:
    positions: set[tuple[int, int]] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list) or not body:
            continue
        first_statement = body[0]
        if (
            isinstance(first_statement, ast.Expr)
            and isinstance(first_statement.value, ast.Constant)
            and isinstance(first_statement.value.value, str)
        ):
            positions.add(
                (first_statement.value.lineno, first_statement.value.col_offset)
            )
    return positions


def _check_tokens(source: str, path: Path, tree: ast.AST) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    docstring_positions = _docstring_positions(tree)
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))

    for token in tokens:
        if token.type != tokenize.STRING:
            continue

        parsed = _string_prefix_and_quote(token.string)
        if parsed is None:
            continue
        prefix, quote = parsed
        position = (token.start[0], token.start[1])
        is_docstring = position in docstring_positions

        if is_docstring and quote != '"""':
            diagnostics.append(
                Diagnostic(path, token.start[0], token.start[1] + 1, "YNG102", "docstring must use triple double quotes")
            )
        elif not is_docstring and "f" not in prefix.lower() and quote in {"'", "'''"}:
            diagnostics.append(
                Diagnostic(path, token.start[0], token.start[1] + 1, "YNG101", "string must use double quotes")
            )

    for line_number, line in enumerate(source.splitlines(), start=1):
        if "\t" in line:
            diagnostics.append(
                Diagnostic(path, line_number, line.index("\t") + 1, "YNG001", "tabs are not allowed")
            )

    return diagnostics


def _check_subscript_quotes(source: str, path: Path, tree: ast.AST) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    lines = source.splitlines()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Subscript):
            continue
        slice_node = node.slice
        if not (
            isinstance(slice_node, ast.Constant)
            and isinstance(slice_node.value, str)
            and hasattr(slice_node, "end_lineno")
            and slice_node.lineno == slice_node.end_lineno
        ):
            continue

        line = lines[slice_node.lineno - 1]
        segment = line[slice_node.col_offset:slice_node.end_col_offset]
        if not segment.startswith("'"):
            diagnostics.append(
                Diagnostic(
                    path,
                    slice_node.lineno,
                    slice_node.col_offset + 1,
                    "YNG103",
                    "dictionary key access must use single quotes"
                )
            )

    return diagnostics


def _check_import_order(path: Path, tree: ast.Module) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]

    previous_kind: int | None = None
    previous_root: str | None = None
    for node in imports:
        kind = 0 if isinstance(node, ast.ImportFrom) else 1
        if previous_kind is not None and kind < previous_kind:
            diagnostics.append(
                Diagnostic(path, node.lineno, node.col_offset + 1, "YNG401", "from imports must appear before plain imports in the same section")
            )

        if isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
        else:
            root = node.names[0].name.split(".")[0]

        if previous_root is not None and kind == previous_kind and root.lower() < previous_root.lower():
            diagnostics.append(
                Diagnostic(path, node.lineno, node.col_offset + 1, "YNG402", "imports must be sorted alphabetically by root module")
            )

        previous_kind = kind
        previous_root = root

    return diagnostics


def lint_code(source: str, path: Path = Path("<string>")) -> list[Diagnostic]:
    """
    Lint Python source and return sorted diagnostics.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return [
            Diagnostic(
                path=path,
                line=error.lineno or 1,
                column=error.offset or 1,
                code="YNG000",
                message=error.msg
            )
        ]

    visitor = StyleGuideVisitor(path=path)
    visitor.visit(tree)

    diagnostics = [
        *visitor.diagnostics,
        *_check_tokens(source=source, path=path, tree=tree),
        *_check_subscript_quotes(source=source, path=path, tree=tree),
        *_check_import_order(path=path, tree=tree)
    ]
    return sorted(diagnostics, key=lambda item: (item.line, item.column, item.code))


def iter_python_files(paths: Sequence[Path]) -> Iterable[Path]:
    """
    Yield Python files from files and directories.
    """
    for path in paths:
        if path.is_file() and path.suffix == ".py":
            yield path
        elif path.is_dir():
            yield from sorted(path.rglob("*.py"))


def lint_path(path: Path) -> list[Diagnostic]:
    """
    Lint one Python file.
    """
    source = path.read_text(encoding="utf-8")
    return lint_code(source=source, path=path)
