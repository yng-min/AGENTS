"""
Style guide linter engine.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from yngfmt.imports import ImportConfig, check_imports


_SNAKE_CASE_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")
_PASCAL_CASE_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]*$")
_BOOLEAN_PREFIXES = ("is_", "has_", "can_", "should_")
_RESULT_FIELDS = {"error", "code", "message", "data"}
_RESULT_ALIASES = {"success", "msg", "payload"}


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
    severity: str = "error"

    def render(self) -> str:
        suffix = " [warning]" if self.severity == "warning" else ""
        return f"{self.path}:{self.line}:{self.column}: {self.code} {self.message}{suffix}"


class StyleGuideVisitor(ast.NodeVisitor):
    """
    Check syntax-aware style guide rules.
    """
    def __init__(self, path: Path) -> None:
        self.path: Path = path
        self.diagnostics: list[Diagnostic] = []

    def add(
        self,
        node: ast.AST,
        code: str,
        message: str,
        severity: str = "error"
    ) -> None:
        self.diagnostics.append(
            Diagnostic(
                path=self.path,
                line=getattr(node, "lineno", 1),
                column=getattr(node, "col_offset", 0) + 1,
                code=code,
                message=message,
                severity=severity
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
        name = _target_name(node.target)
        if name is not None and _is_boolean_annotation(node.annotation):
            self._check_boolean_name(node=node, name=name)
        self.generic_visit(node)

    def _check_boolean_name(self, node: ast.AST, name: str) -> None:
        if name.startswith(_BOOLEAN_PREFIXES):
            return
        self.add(
            node,
            "YNG203",
            "boolean name could use is_/has_/can_/should_ prefix",
            severity="warning"
        )

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
                continue
            if _is_boolean_annotation(argument.annotation):
                self._check_boolean_name(node=argument, name=argument.arg)

        if node.args.vararg is not None and node.args.vararg.annotation is None:
            self.add(node.args.vararg, "YNG301", "*args type annotation is missing")
        if node.args.kwarg is not None and node.args.kwarg.annotation is None:
            self.add(node.args.kwarg, "YNG301", "**kwargs type annotation is missing")
        if node.returns is None:
            self.add(node, "YNG302", "return type annotation is missing")


def _target_name(target: ast.expr) -> str | None:
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


def _is_none_annotation(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Constant)
        and node.value is None
        or isinstance(node, ast.Name)
        and node.id == "None"
    )


def _is_boolean_annotation(node: ast.expr) -> bool:
    if isinstance(node, ast.Name):
        return node.id == "bool"
    if isinstance(node, ast.Attribute):
        return node.attr == "bool"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return (
            _is_boolean_annotation(node.left)
            and _is_none_annotation(node.right)
            or _is_none_annotation(node.left)
            and _is_boolean_annotation(node.right)
        )
    if isinstance(node, ast.Subscript):
        value = node.value
        is_optional = (
            isinstance(value, ast.Name)
            and value.id == "Optional"
            or isinstance(value, ast.Attribute)
            and value.attr == "Optional"
        )
        return is_optional and _is_boolean_annotation(node.slice)
    return False


def _string_prefix_and_quote(token_value: str) -> tuple[str, str] | None:
    match = re.match(r"(?i)^([rubf]*)(\"\"\"|'''|\"|')", token_value)
    if match is None:
        return None
    return match.group(1), match.group(2)


def _is_docstring_statement(node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _docstring_positions(tree: ast.AST) -> set[tuple[int, int]]:
    positions: set[tuple[int, int]] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list) or not body:
            continue
        first_statement = body[0]
        if _is_docstring_statement(first_statement):
            positions.add((first_statement.value.lineno, first_statement.value.col_offset))
    return positions


def _subscript_string_positions(tree: ast.AST) -> set[tuple[int, int]]:
    positions: set[tuple[int, int]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Subscript):
            continue
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            positions.add((node.slice.lineno, node.slice.col_offset))
    return positions


def _check_tokens(source: str, path: Path, tree: ast.AST) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    docstring_positions = _docstring_positions(tree)
    subscript_positions = _subscript_string_positions(tree)
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
                Diagnostic(
                    path,
                    token.start[0],
                    token.start[1] + 1,
                    "YNG102",
                    "docstring must use triple double quotes"
                )
            )
        elif (
            not is_docstring
            and position not in subscript_positions
            and "f" not in prefix.lower()
            and quote in {"'", "'''"}
        ):
            diagnostics.append(
                Diagnostic(
                    path,
                    token.start[0],
                    token.start[1] + 1,
                    "YNG101",
                    "string must use double quotes"
                )
            )

    for line_number, line in enumerate(source.splitlines(), start=1):
        if "\t" in line:
            diagnostics.append(
                Diagnostic(
                    path,
                    line_number,
                    line.index("\t") + 1,
                    "YNG001",
                    "tabs are not allowed"
                )
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


def _blank_lines_between(previous: ast.AST, current: ast.AST) -> int:
    previous_end = getattr(previous, "end_lineno", getattr(previous, "lineno", 1))
    current_start = getattr(current, "lineno", previous_end + 1)
    return max(0, current_start - previous_end - 1)


def _first_code_line(node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    decorator_lines = [decorator.lineno for decorator in node.decorator_list]
    return min(decorator_lines, default=node.lineno)


def _check_docstring_layout(tree: ast.Module, path: Path) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []

    if tree.body and _is_docstring_statement(tree.body[0]) and len(tree.body) > 1:
        docstring = tree.body[0]
        if _blank_lines_between(docstring, tree.body[1]) != 1:
            diagnostics.append(
                Diagnostic(
                    path,
                    docstring.lineno,
                    docstring.col_offset + 1,
                    "YNG104",
                    "module docstring must be followed by exactly one blank line"
                )
            )

    for node in ast.walk(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.body or not _is_docstring_statement(node.body[0]) or len(node.body) == 1:
            continue
        docstring = node.body[0]
        next_statement = node.body[1]
        if _blank_lines_between(docstring, next_statement) == 0:
            continue
        code = "YNG105" if isinstance(node, ast.ClassDef) else "YNG106"
        subject = "class" if isinstance(node, ast.ClassDef) else "function"
        diagnostics.append(
            Diagnostic(
                path,
                next_statement.lineno,
                next_statement.col_offset + 1,
                code,
                f"{subject} docstring must not be followed by a blank line"
            )
        )
    return diagnostics


def _definition_header_end_line(
    source: str,
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
) -> int:
    lines = source.splitlines(keepends=True)
    fragment = "".join(lines[node.lineno - 1:])
    depth = 0
    for token in tokenize.generate_tokens(io.StringIO(fragment).readline):
        if token.type != tokenize.OP:
            continue
        if token.string in {"(", "[", "{"}:
            depth += 1
        elif token.string in {")", "]", "}"}:
            depth -= 1
        elif token.string == ":" and depth == 0:
            return node.lineno + token.end[0] - 1
    return node.lineno


def _check_definition_spacing(
    source: str,
    tree: ast.Module,
    path: Path
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    definitions = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)

    for previous, current in zip(tree.body, tree.body[1:]):
        if not isinstance(current, definitions):
            continue
        previous_end = previous.end_lineno or previous.lineno
        blank_lines = _first_code_line(current) - previous_end - 1
        if blank_lines != 2:
            diagnostics.append(
                Diagnostic(
                    path,
                    _first_code_line(current),
                    1,
                    "YNG401",
                    "top-level definition must be preceded by two blank lines"
                )
            )

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.body:
            continue
        header_end = _definition_header_end_line(source=source, node=node)
        if node.body[0].lineno - header_end - 1 > 0:
            diagnostics.append(
                Diagnostic(
                    path,
                    node.body[0].lineno,
                    node.body[0].col_offset + 1,
                    "YNG403",
                    "function body must start immediately after the declaration"
                )
            )

    for class_node in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
        body = class_node.body
        start_index = 1 if body and _is_docstring_statement(body[0]) else 0
        methods = [
            node
            for node in body[start_index:]
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        for previous, current in zip(methods, methods[1:]):
            previous_end = previous.end_lineno or previous.lineno
            blank_lines = _first_code_line(current) - previous_end - 1
            if blank_lines != 1:
                diagnostics.append(
                    Diagnostic(
                        path,
                        _first_code_line(current),
                        current.col_offset + 1,
                        "YNG402",
                        "class methods must be separated by one blank line"
                    )
                )
    return diagnostics


def _body_without_docstring(
    node: ast.FunctionDef | ast.AsyncFunctionDef
) -> list[ast.stmt]:
    if node.body and _is_docstring_statement(node.body[0]):
        return node.body[1:]
    return node.body


def _is_call_statement(node: ast.stmt) -> bool:
    if not isinstance(node, ast.Expr):
        return False
    value = node.value
    if isinstance(value, ast.Await):
        value = value.value
    return isinstance(value, ast.Call)


def _check_wrapper_and_return_spacing(tree: ast.Module, path: Path) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = _body_without_docstring(node)
        if len(body) == 2 and _is_call_statement(body[0]) and isinstance(body[1], ast.Return):
            if _blank_lines_between(body[0], body[1]) > 0:
                diagnostics.append(
                    Diagnostic(
                        path,
                        body[1].lineno,
                        body[1].col_offset + 1,
                        "YNG501",
                        "short wrapper preparation and delegation must remain adjacent"
                    )
                )

        for previous, current in zip(body, body[1:]):
            if not isinstance(current, ast.Return) or _blank_lines_between(previous, current) == 0:
                continue
            target_name: str | None = None
            if isinstance(previous, (ast.Assign, ast.AnnAssign)):
                target = previous.targets[0] if isinstance(previous, ast.Assign) else previous.target
                target_name = _target_name(target)
            if target_name is None or not isinstance(current.value, ast.Name):
                continue
            if current.value.id != target_name:
                continue
            diagnostics.append(
                Diagnostic(
                    path,
                    current.lineno,
                    current.col_offset + 1,
                    "YNG502",
                    "return must remain adjacent to the statement producing its value"
                )
            )
    return diagnostics


def _dictionary_string_keys(node: ast.Dict) -> set[str] | None:
    keys: set[str] = set()
    for key in node.keys:
        if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
            return None
        keys.add(key.value)
    return keys


def _check_result_objects(tree: ast.Module, path: Path) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Return) or not isinstance(node.value, ast.Dict):
            continue
        keys = _dictionary_string_keys(node.value)
        if keys is None:
            continue
        if keys & _RESULT_ALIASES:
            diagnostics.append(
                Diagnostic(
                    path,
                    node.lineno,
                    node.col_offset + 1,
                    "YNG602",
                    "result dictionary uses non-standard field names"
                )
            )
            continue
        if not keys & _RESULT_FIELDS:
            continue
        missing = sorted(_RESULT_FIELDS - keys)
        if missing:
            diagnostics.append(
                Diagnostic(
                    path,
                    node.lineno,
                    node.col_offset + 1,
                    "YNG601",
                    f"result dictionary is missing required fields: {', '.join(missing)}"
                )
            )
    return diagnostics


def lint_code(
    source: str,
    path: Path = Path("<string>"),
    import_config: ImportConfig = ImportConfig()
) -> list[Diagnostic]:
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
    import_diagnostics = [
        Diagnostic(
            path=path,
            line=issue.line,
            column=issue.column,
            code=issue.code,
            message=issue.message
        )
        for issue in check_imports(source=source, config=import_config)
    ]
    diagnostics = [
        *visitor.diagnostics,
        *_check_tokens(source=source, path=path, tree=tree),
        *_check_subscript_quotes(source=source, path=path, tree=tree),
        *_check_docstring_layout(tree=tree, path=path),
        *_check_definition_spacing(source=source, tree=tree, path=path),
        *_check_wrapper_and_return_spacing(tree=tree, path=path),
        *_check_result_objects(tree=tree, path=path),
        *import_diagnostics
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


def lint_path(
    path: Path,
    import_config: ImportConfig = ImportConfig()
) -> list[Diagnostic]:
    """
    Lint one Python file.
    """
    source = path.read_text(encoding="utf-8")
    return lint_code(source=source, path=path, import_config=import_config)
